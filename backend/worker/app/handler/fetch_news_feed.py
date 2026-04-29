import logging
from typing import Any, Mapping

from app.core.util.datetime import utcnow, datetime_to_epoch_ms
from app.core.constants import OutboxEventType, LOCK
from app.runtime.app_context import WorkerContext
from app.util.utils import require, try_acquire_lock, release_lock
from app.exception_handlers import SkipHandler, FatalHandler

logger = logging.getLogger(__name__)

def handle_fetch_news_feed(
    ctx: WorkerContext,
    payload: Mapping[str, Any],
) -> dict[str, Any]: 
    interval_sec = int(require(payload, "interval_sec", target="payload.interval_sec"))
    slot = int(require(payload, "slot", target="payload.slot"))
    news_feed = require(payload, "news_feed", target="payload.news_feed")
    rss_source_id = require(news_feed, "rss_source_id", target="news_feed.rss_source_id")
    rss_source_code = require(news_feed, "rss_source_code", target="news_feed.rss_source_code")

    job_config = ctx.config.worker_jobs[OutboxEventType.FETCH_NEWS_FEED.value]

    app_name = ctx.config.app_name
    deploy_env = ctx.config.deploy_env
    batch_size = job_config["batch_size"]
    run_key = job_config["run_key"]
    lock_key = f"{app_name}:{deploy_env}:{LOCK}:{run_key}:{rss_source_id}:{slot}:{interval_sec}"
    token = try_acquire_lock(
        ctx.redis_client,
        lock_key,
        ttl_sec=ctx.config.outbox_send_lock_ttl_sec,
    )
    if not token:
        raise SkipHandler("locked")

    try:
        result = ctx.svcs.newses.fetch_news_feed(
            slot=slot,
            rss_source_id=rss_source_id, 
            rss_source_code=rss_source_code, 
            batch_size=batch_size
        )

        logger.info(
            "fetch_news_feed",
        )
        return result

    except Exception as e:
        raise FatalHandler(
            "fetch_news_feeds_fatal",
            meta={"error": str(e), "interval_sec": interval_sec, "slot": slot},
        ) from e
    finally:
        release_lock(ctx.redis_client, lock_key, token)