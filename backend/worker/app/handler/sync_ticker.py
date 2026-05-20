from typing import Any, Mapping
import logging

from app.core.util.datetime import utcnow, datetime_to_epoch_ms
from app.core.constants import OutboxEventType, LOCK, META
from app.runtime.app_context import WorkerContext
from app.util.utils import require, try_acquire_lock, release_lock
from app.exception_handlers import SkipHandler, FatalHandler, RetryHandler

logger = logging.getLogger(__name__)


def handle_sync_tickers(
    ctx: WorkerContext,
    payload: Mapping[str, Any],
) -> dict[str, Any]:
    redis_key_prefix = f"{{{ctx.config.key_prefix}}}"
    
    slot = int(require(payload, "slot", target="payload.slot"))
    requested_at_epoch = int(
        require(payload, "requested_at_epoch", target="payload.requested_at_epoch")
    )
    interval_sec = int(require(payload, "interval_sec", target="payload.interval_sec"))
    job_config = ctx.config.worker_jobs[OutboxEventType.SYNC_TICKERS.value]
    run_key = job_config["run_key"]

    lock_key = f"{redis_key_prefix}:{LOCK}:{run_key}:{slot}:{interval_sec}"

    token = try_acquire_lock(
        ctx.redis_client, lock_key, ttl_sec=ctx.config.outbox_send_lock_ttl_sec
    )
    if not token:
        raise SkipHandler("locked")

    logger.info(
        "handle_sync_tickers start slot=%s interval_sec=%s",
        slot,
        interval_sec,
    )

    try:
        # compute 24h ticker stats from price_snapshots and update ticker table
        total = ctx.svcs.markets.sync_exchange_instruments_tickers()

        processed_at = datetime_to_epoch_ms(utcnow())
        result = {
            "count": total,
            "slot": slot,
            "requested_at_epoch": requested_at_epoch,
            "processed_at": processed_at,
        }

        logger.info(
            "handle_sync_tickers done slot=%s interval_sec=%s", slot, interval_sec
        )
        return result

    except SkipHandler:
        # 스킵 핸들러도 그대로 전달
        raise
    except Exception as e:
        raise FatalHandler(
            "sync_tickers_fatal",
            meta={"error": str(e)},
        ) from e
    finally:
        release_lock(ctx.redis_client, lock_key, token)
