import logging
from typing import Any, Mapping

from app.core.util.datetime import utcnow, datetime_to_epoch_ms
from app.core.constants import LanguageCode, OutboxEventType, LOCK
from app.runtime.app_context import WorkerContext
from app.util.utils import require, try_acquire_lock, release_lock
from app.exception_handlers import SkipHandler, FatalHandler

logger = logging.getLogger(__name__)

def handle_translate_news_items(
    ctx: WorkerContext,
    payload: Mapping[str, Any],
) -> dict[str, Any]: 
    redis_key_prefix = f"{{{ctx.config.key_prefix}}}"

    rss_source_id = require(payload, "rss_source_id", target="payload.rss_source_id")
    rss_source_code = require(
        payload, "rss_source_code", target="payload.rss_source_code"
    )
    locale_value = require(
        payload, "locale", target="payload.locale"
    )

    job_config = ctx.config.worker_jobs[OutboxEventType.TRANSLATE_NEWS_ITEMS.value]
    batch_size = job_config["batch_size"]
    run_key = job_config["run_key"]

    lock_key = (
        f"{redis_key_prefix}:{LOCK}:{run_key}:{rss_source_id}:{locale_value}"
    )
    token = try_acquire_lock(
        ctx.redis_client, lock_key, ttl_sec=ctx.config.outbox_send_lock_ttl_sec
    )
    if not token:
        raise SkipHandler("locked")

    try:
        result = ctx.svcs.newses.translate_news_items(
            rss_source_id=rss_source_id,
            rss_source_code=rss_source_code,
            locale=LanguageCode(locale_value),
            batch_size=batch_size,
        )

        logger.info(
            "translate_news_items",
        )
        return result

    # TODO: 추후 수동, 자동 재시도 정책
    # except (TimeoutError, ConnectionError) as e:
    #     raise RetryHandler(
    #         "news_translation_retry",
    #         meta={"provider": "TRANSLATE", "error": str(e)},
    #     ) from e

    except Exception as e:
        raise FatalHandler(
            "news_translation_fetal",
            meta={"provider": "TRANSLATE", "error": str(e)},
        ) from e
    finally:
        release_lock(ctx.redis_client, lock_key, token)

