import json
import uuid
import logging
from typing import Any, Mapping
from app.core.util.datetime import utcnow, to_epoch_ms
from app.core.constants import OutboxEventType
from app.runtime.app_context import WorkerContext
from app.util.utils import require, try_acquire_lock, release_lock
from app.exception_handlers import SkipHandler, RetryHandler, FatalHandler

logger = logging.getLogger(__name__)


def handle_sync_exchanges(
    ctx: WorkerContext, payload: Mapping[str, Any]
) -> dict[str, Any]:
    started_at = utcnow()
    job_config = ctx.config.worker_jobs[OutboxEventType.SYNC_EXCHANGES.value]
    app_name = ctx.config.app_name
    deploy_env = ctx.config.deploy_env
    batch_size = job_config["batch_size"]
    ttl_sec = job_config["ttl_sec"]
    run_key = job_config["run_key"]
    redis_key = f"{app_name}:{deploy_env}:snap:{run_key}"

    r = ctx.redis_client.conn()
    run_id = uuid.uuid4().hex
    tmp_key = f"{app_name}:{deploy_env}:tmp:{run_key}:{run_id}"

    total = 0
    offset = 0

    lock_key = f"{app_name}:{deploy_env}:lock:{run_key}"
    token = try_acquire_lock(
        ctx.redis_client, lock_key, ttl_sec=ctx.config.outbox_send_lock_ttl_sec
    )
    if not token:
        raise SkipHandler("locked")

    try:
        pipe = r.pipeline(transaction=False)
        pipe.delete(tmp_key)

        while True:
            exchanges = ctx.svcs.markets.list_exchanges_by_filter(
                limit=batch_size, offset=offset
            )
            if not exchanges:
                break

            mapping = {}
            for ex in exchanges:
                mapping[ex.code] = json.dumps(
                    _exchange_to_payload(ex), ensure_ascii=False, separators=(",", ":")
                )

            pipe.hset(tmp_key, mapping=mapping)
            total += len(exchanges)
            offset += len(exchanges)

            # 파이프라인을 너무 크게 잡지 않도록 배치 단위로 flush
            pipe.execute()

        # metadata(선택)
        meta_key = f"{app_name}:{deploy_env}:meta:{run_key}"

        pipe = r.pipeline(transaction=False)
        pipe.hset(
            meta_key,
            mapping={"started_at": to_epoch_ms(started_at), "count": total},
        )

        # TTL이 필요하면 tmp/meta 둘 다 TTL 적용
        if ttl_sec > 0:
            pipe.expire(tmp_key, ttl_sec)
            pipe.expire(meta_key, ttl_sec)

        pipe.execute()

        # 원자적 스왑: tmp_key -> redis_key
        # - rename은 원자적, 기존 redis_key가 있으면 덮어씀
        r.rename(tmp_key, redis_key)

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
    return {
        "id": getattr(ex, "id", None),
        "code": getattr(ex, "code", None),
        "name": getattr(ex, "name", None),
        "is_active": getattr(ex, "is_active", None),
    }
