import json
import logging
from typing import Any, Mapping

from app.core.util.datetime import utcnow, datetime_to_epoch_ms
from app.core.constants import OutboxEventType, SNAP, META, TMP, LOCK
from app.runtime.app_context import WorkerContext
from app.util.utils import require, try_acquire_lock, release_lock
from app.exception_handlers import SkipHandler, FatalHandler

logger = logging.getLogger(__name__)


def handle_sync_exchanges(
    ctx: WorkerContext, payload: Mapping[str, Any]
) -> dict[str, Any]:
    redis_key_prefix = f"{{{ctx.config.key_prefix}}}"
    started_at = utcnow()

    interval_sec = int(require(payload, "interval_sec", target="payload.interval_sec"))
    slot = int(require(payload, "slot", target="payload.slot"))

    job_config = ctx.config.worker_jobs[OutboxEventType.SYNC_EXCHANGES.value]

    batch_size = job_config["batch_size"]
    ttl_sec = job_config["ttl_sec"]
    run_key = job_config["run_key"]

    redis_key = f"{redis_key_prefix}:{SNAP}:{run_key}"
    tmp_key = f"{redis_key_prefix}:{TMP}:{run_key}:{slot}:{interval_sec}"
    lock_key = f"{redis_key_prefix}:{LOCK}:{run_key}:{slot}:{interval_sec}"
    meta_key = f"{redis_key_prefix}:{META}:{run_key}"

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

        while True:
            exchanges = ctx.svcs.markets.list_exchange_by_filter(
                limit=batch_size, offset=offset
            )

            if not exchanges:
                break

            mapping: dict[str, str] = {}

            for ex in exchanges:
                mapping[ex.code] = json.dumps(
                    _exchange_to_payload(ex), ensure_ascii=False, separators=(",", ":")
                )

            if mapping:
                # 파이프라인을 너무 크게 잡지 않도록 배치 단위로 flush
                pipe = r.pipeline(transaction=False)
                pipe.hset(tmp_key, mapping=mapping)
                pipe.execute()
                total += len(mapping)

            offset += batch_size

        finished_at = utcnow()
        started_epoch_ms = datetime_to_epoch_ms(started_at)
        finished_epoch_ms = datetime_to_epoch_ms(finished_at)

        if total > 0:
            # 원자적 스왑: tmp_key -> redis_key
            r.rename(tmp_key, redis_key)
        else:
            r.delete(redis_key)

        meta = {
            "run_key": run_key,
            "slot": slot,
            "interval_sec": interval_sec,
            "total": total,
            "started_at_epoch_ms": started_epoch_ms,
            "synced_at_epoch_ms": finished_epoch_ms,
        }

        r.set(
            meta_key,
            json.dumps(
                meta,
                ensure_ascii=False,
                separators=(",", ":"),
            ),
        )

        # TTL이 필요하면 tmp/meta 둘 다 TTL 적용
        # if ttl_sec > 0:
        #     pipe.expire(tmp_key, ttl_sec)
        #     pipe.expire(meta_key, ttl_sec)

        logger.info(
            "sync_exchanges: wrote %s exchanges into redis_key=%s", total, redis_key
        )

        return {"count": total, "redis_key": redis_key, "ttl_sec": ttl_sec}
    except Exception as e:
        raise FatalHandler(
            "sync_exchanges_fatal",
            meta={"error": str(e)},
        ) from e
    finally:
        release_lock(ctx.redis_client, lock_key, token)


def _exchange_to_payload(ex: Any) -> dict[str, Any]:
    """
    DTO/엔티티 형태를 (duck-typing) Redis에 저장할 최소 필드만 뽑는다.
    """
    return {"id": ex.id, "is_active": ex.is_active}
