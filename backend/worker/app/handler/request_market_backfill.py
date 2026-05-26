from typing import Any, Mapping
from app.core.constants import OutboxEventType, LOCK
from app.core.util.datetime import utcnow, ensure_utc
from app.runtime.app_context import WorkerContext
from app.util.utils import require, try_acquire_lock, release_lock
from app.exception_handlers import SkipHandler, RetryHandler, FatalHandler


def handle_request_market_backfills(
    ctx: WorkerContext,
    payload: Mapping[str, Any],
) -> dict[str, Any]: 
    redis_key_prefix = f"{{{ctx.config.key_prefix}}}"
    
    backfill_request_id = int(require(payload, "backfill_request_id", target="payload.backfill_request_id"))
    job_config = ctx.config.worker_jobs[OutboxEventType.REQUEST_MARKET_BACKFILL.value]
    run_key = job_config["run_key"]
    job_batch_size = job_config["job_batch_size"]
    api_batch_size = job_config["api_batch_size"]

    if job_batch_size <= 0:
        raise FatalHandler(
            "invalid_market_backfill_job_batch_size",
            meta={"job_batch_size": job_batch_size},
        )

    if api_batch_size <= 0:
        raise FatalHandler(
            "invalid_market_backfill_api_batch_size",
            meta={"api_batch_size": api_batch_size},
        )
    
    lock_key = f"{redis_key_prefix}:{LOCK}:{run_key}:{backfill_request_id}"
    token = try_acquire_lock(
        ctx.redis_client, key=lock_key, ttl_sec=ctx.config.outbox_send_lock_ttl_sec
    )
    if not token:
        raise SkipHandler("locked")

    try:
        return ctx.svcs.markets.request_market_backfills(
            backfill_request_id=backfill_request_id,
            job_batch_size=job_batch_size,
            api_batch_size=api_batch_size,
        )
    except SkipHandler:
        # 스킵 핸들러도 그대로 전달
        raise
    except Exception as e:
        raise FatalHandler(
            "request_market_backfills_fatal",
            meta={"error": str(e)},
        ) from e
    finally:
        release_lock(ctx.redis_client, lock_key, token)

