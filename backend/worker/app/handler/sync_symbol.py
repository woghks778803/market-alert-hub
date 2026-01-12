import logging
import uuid
from typing import Any, Callable, Mapping
from app.core.util.datetime import utcnow, to_epoch_ms
from app.core.constants import OutboxEventType
from app.runtime.app_context import WorkerContext
from app.util.utils import require, try_acquire_lock, release_lock
from app.exception_handlers import SkipHandler, FatalHandler, RetryHandler

logger = logging.getLogger(__name__)


def handle_sync_symbols(
    ctx: WorkerContext,
    payload: Mapping[str, Any],
) -> Any:
    started_at = utcnow()
    job_config = ctx.config.worker_jobs[OutboxEventType.SYNC_SYMBOLS.value]
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

        # ctx.svcs.markets.sync_exchange_instruments_from_upbit()

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

        r.rename(tmp_key, redis_key)

        return {"ok": True}
    except Exception as e:
        raise FatalHandler(
            "sync_symbols_fatal",
            meta={"error": str(e)},
        ) from e
    finally:
        release_lock(ctx.redis_client, lock_key, token)
