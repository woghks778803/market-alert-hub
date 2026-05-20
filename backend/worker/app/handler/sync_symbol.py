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
    redis_key_prefix = f"{{{ctx.config.key_prefix}}}"
    started_at = utcnow()

    interval_sec = int(require(payload, "interval_sec", target="payload.interval_sec"))
    slot = int(require(payload, "slot", target="payload.slot"))
    exchange = require(payload, "exchange", target="payload.exchange")
    ex_code = require(exchange, "code", target="exchange.code")

    job_config = ctx.config.worker_jobs[OutboxEventType.SYNC_SYMBOLS.value]

    batch_size = job_config["batch_size"]
    ttl_sec = job_config["ttl_sec"]
    run_key = job_config["run_key"]

    redis_key = f"{redis_key_prefix}:{SNAP}:{run_key}:{ex_code}"
    tmp_key = f"{redis_key_prefix}:{TMP}:{run_key}:{ex_code}:{slot}:{interval_sec}"
    lock_key = (
        f"{redis_key_prefix}:{LOCK}:{run_key}:{ex_code}:{slot}:{interval_sec}"
    )
    meta_key = f"{redis_key_prefix}:{META}:{run_key}:{ex_code}"

    token = try_acquire_lock(
        ctx.redis_client, lock_key, ttl_sec=ctx.config.outbox_send_lock_ttl_sec
    )
    if not token:
        raise SkipHandler("locked")

    total = 0
    offset = 0
    
    try:
        r = ctx.redis_client.conn()
        r.delete(tmp_key)

        exchange_instruments = ctx.svcs.markets.sync_exchange_instruments(exchange_code=ex_code)

        mapping: dict[str, str] = {}
        for row in exchange_instruments:
            sym = getattr(row, "exchange_symbol", None)
            if not sym:
                continue
            mapping[sym] = json.dumps(
                _exchange_instrument_to_payload(row),
                ensure_ascii=False,
                separators=(",", ":"),
            )

        if mapping:
            pipe = r.pipeline(transaction=False)
            pipe.hset(tmp_key, mapping=mapping)
            pipe.execute()
            total += len(mapping)
        
        offset += batch_size

        finished_at = utcnow()
        started_epoch_ms = datetime_to_epoch_ms(started_at)
        finished_epoch_ms = datetime_to_epoch_ms(finished_at)
        
        meta = {
            "run_key": run_key,
            "slot": slot,
            "interval_sec": interval_sec,
            "total": total,
            "started_at_epoch_ms": started_epoch_ms,
            "synced_at_epoch_ms": finished_epoch_ms,
        }

        pipe = r.pipeline(transaction=False)
        pipe.set(
            meta_key,
            json.dumps(
                meta,
                ensure_ascii=False,
                separators=(",", ":"),
            ),
        )

        if total > 0:
            pipe.rename(tmp_key, redis_key)
        else:
            pipe.delete(redis_key)

        # TTL이 필요하면 tmp/meta 둘 다 TTL 적용
        # if ttl_sec > 0:
        #     pipe.expire(tmp_key, ttl_sec)
        #     pipe.expire(meta_key, ttl_sec)
        pipe.execute()

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
    (MarketSimple 기준 필드)
    """
    return {
        "exchange_instrument_id": row.exchange_instrument_id,
        "base_asset_id": row.base_asset_id,
        "quote_asset_id": row.quote_asset_id,
    }
