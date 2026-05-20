import logging
from typing import Any, Mapping

from app.core.constants import OutboxEventType, UserStatus, LOCK
from app.runtime.app_context import WorkerContext
from app.util.utils import require, try_acquire_lock, release_lock
from app.exception_handlers import (
    SkipHandler,
    FatalHandler,
)

logger = logging.getLogger(__name__)


def handle_cleanup_deleted_users(
    ctx: WorkerContext,
    payload: Mapping[str, Any],
) -> dict[str, Any]:
    redis_key_prefix = f"{{{ctx.config.key_prefix}}}"

    interval_sec = int(require(payload, "interval_sec", target="payload.interval_sec"))
    slot = int(require(payload, "slot", target="payload.slot"))
    job_config = ctx.config.worker_jobs[OutboxEventType.CLEANUP_DELETED_USERS.value]
    run_key = job_config["run_key"]

    lock_key = f"{redis_key_prefix}:{LOCK}:{run_key}:{slot}:{interval_sec}"
    token = try_acquire_lock(
        ctx.redis_client, lock_key, ttl_sec=ctx.config.outbox_send_lock_ttl_sec
    )
    if not token:
        raise SkipHandler("locked")

    try:
        result = ctx.svcs.auths.cleanup_deleted_users()

        logger.info(
            "cleanup_deleted_users processed_count=%s start_date=%s end_date=%s",
            getattr(result, "processed_count", None),
            getattr(result, "start_date", None),
            getattr(result, "end_date", None),
        )
        return result

    except Exception as e:
        raise FatalHandler(
            "cleanup_deleted_users_fatal",
            meta={"error": str(e), "interval_sec": interval_sec, "slot": slot},
        ) from e
    finally:
        release_lock(ctx.redis_client, lock_key, token)
