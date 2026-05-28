import logging
from typing import Any, Mapping

from app.core.constants import OutboxEventType, LOCK
from app.runtime.app_context import WorkerContext
from app.util.utils import require, try_acquire_lock, release_lock
from app.exception_handlers import (
    SkipHandler,
    FatalHandler,
)

logger = logging.getLogger(__name__)


def handle_unlink_oauth_accounts(
    ctx: WorkerContext,
    payload: Mapping[str, Any],
) -> dict[str, Any]:
    redis_key_prefix = f"{{{ctx.config.key_prefix}}}"

    user_id = require(payload, "user_id", target="payload.user_id")
    job_config = ctx.config.worker_jobs[OutboxEventType.UNLINK_OAUTH_ACCOUNTS.value]
    run_key = job_config["run_key"]

    lock_key = f"{redis_key_prefix}:{LOCK}:{run_key}:{user_id}"
    token = try_acquire_lock(
        ctx.redis_client, lock_key, ttl_sec=ctx.config.outbox_send_lock_ttl_sec
    )
    if not token:
        raise SkipHandler("locked")

    try:
        result = ctx.svcs.auths.oauth_unlink(user_id=user_id)

        logger.info(
            "unlink_oauth_accounts user_id=%s processed_count=%s",
            result["user_id"],
            result["processed_count"],
        )
        return result

    except Exception as e:
        raise FatalHandler(
            "unlink_oauth_accounts_fatal",
            meta={"error": str(e), "user_id": user_id},
        ) from e
    finally:
        release_lock(ctx.redis_client, lock_key, token)
