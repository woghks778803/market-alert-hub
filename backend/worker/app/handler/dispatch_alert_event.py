import json
import logging
from typing import Any, Mapping

from app.core.util.datetime import utcnow
from app.core.constants import OutboxEventType, LOCK
from app.runtime.app_context import WorkerContext
from app.util.utils import require, try_acquire_lock, release_lock
from app.exception_handlers import SkipHandler, FatalHandler, RetryHandler

logger = logging.getLogger(__name__)


def handle_dispatch_alert_events(
    ctx: WorkerContext,
    payload: Mapping[str, Any],
) -> dict[str, Any]: 
    interval_sec = int(require(payload, "interval_sec", target="payload.interval_sec"))
    slot = int(require(payload, "slot", target="payload.slot"))
    job_config = ctx.config.worker_jobs[OutboxEventType.DISPATCH_ALERT_EVENTS.value]
    app_name = ctx.config.app_name
    deploy_env = ctx.config.deploy_env
    batch_size = job_config["batch_size"]
    run_key = job_config["run_key"]

    lock_key = f"{app_name}:{deploy_env}:{LOCK}:{run_key}:{slot}:{interval_sec}"
    token = try_acquire_lock(
        ctx.redis_client, lock_key, ttl_sec=ctx.config.outbox_send_lock_ttl_sec
    )
    if not token:
        raise SkipHandler("locked")

    try:
        result = ctx.svcs.alerts.dispatch_alert_events(batch_size)

        logger.info(
            "dispatch_alert_events",
        )
        return result

    except Exception as e:
        raise FatalHandler(
            "dispatch_alert_events_fatal",
            meta={"error": str(e), "interval_sec": interval_sec, "slot": slot},
        ) from e
    finally:
        release_lock(ctx.redis_client, lock_key, token)
