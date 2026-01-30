import logging
import json
from typing import Any, Callable, Mapping
from app.core.util.datetime import utcnow, datetime_to_epoch_ms
from app.core.constants import OutboxEventType, SNAP, META, TMP, LOCK
from app.runtime.app_context import WorkerContext
from app.util.utils import require, try_acquire_lock, release_lock
from app.exception_handlers import SkipHandler, FatalHandler, RetryHandler

logger = logging.getLogger(__name__)


def handle_sync_symbols(
    ctx: WorkerContext,
    payload: Mapping[str, Any],
) -> dict[str, Any]:
    started_at = utcnow()
    interval_sec = int(require(payload, "interval_sec", target="payload.interval_sec"))
    slot = int(require(payload, "slot", target="payload.slot"))
    job_config = ctx.config.worker_jobs[OutboxEventType.SYNC_SYMBOLS.value]
    app_name = ctx.config.app_name
    deploy_env = ctx.config.deploy_env
    batch_size = job_config["batch_size"]
    ttl_sec = job_config["ttl_sec"]
    run_key = job_config["run_key"]
    redis_key = f"{app_name}:{deploy_env}:{SNAP}:{run_key}"

    total = 0
    offset = 0

    r = ctx.redis_client.conn()
    tmp_key = f"{app_name}:{deploy_env}:{TMP}:{run_key}:{slot}:{interval_sec}"
    meta_key = f"{app_name}:{deploy_env}:{META}:{run_key}"
    lock_key = f"{app_name}:{deploy_env}:{LOCK}:{run_key}:{slot}:{interval_sec}"
    token = try_acquire_lock(
        ctx.redis_client, lock_key, ttl_sec=ctx.config.outbox_send_lock_ttl_sec
    )
    if not token:
        raise SkipHandler("locked")

    try:
        exchange_instruments = ctx.svcs.markets.sync_exchange_instruments_from_upbit()

        pipe = r.pipeline(transaction=False)
        pipe.delete(tmp_key)

        mapping: dict[str, str] = {}
        total = 0
        for row in exchange_instruments:
            sym = getattr(row, "exchange_symbol", None)
            if not sym:
                continue
            mapping[sym] = json.dumps(
                _exchange_instrument_to_payload(row),
                ensure_ascii=False,
                separators=(",", ":"),
            )
            total += 1

        if mapping:
            pipe.hset(tmp_key, mapping=mapping)

        pipe.hset(
            meta_key,
            mapping={"started_at": datetime_to_epoch_ms(started_at), "count": total},
        )

        # TTL이 필요하면 tmp/meta 둘 다 TTL 적용
        # if ttl_sec > 0:
        #     pipe.expire(tmp_key, ttl_sec)
        #     pipe.expire(meta_key, ttl_sec)

        pipe.execute()

        r.rename(tmp_key, redis_key)

        logger.info(
            "sync_symbols: wrote %s exchange_instruments into redis_key=%s",
            total,
            redis_key,
        )

        return {"count": total, "redis_key": redis_key, "ttl_sec": ttl_sec}
    except Exception as e:
        raise FatalHandler(
            "sync_symbols_fatal",
            meta={"error": str(e)},
        ) from e
    finally:
        release_lock(ctx.redis_client, lock_key, token)


def _exchange_instrument_to_payload(row: Any) -> dict[str, Any]:
    """
    DTO/엔티티/ORM 어떤 형태든 duck-typing으로 Redis snapshot에 넣을 payload로 변환.
    (MappingItem 기준 필드)
    """
    return {
        "id": row.id,
        "base_asset_id": row.base_asset_id,
        "quote_asset_id": row.quote_asset_id,
    }
