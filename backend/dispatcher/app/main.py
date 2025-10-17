import time
import logging
from rq import Queue
from redis import Redis
from app.runtime.settings import settings
from app.core.logging import setup_logging
from app.deps import get_services

logger = logging.getLogger("dispatcher")


def main() -> None:
    setup_logging()
    logger.info(
        "Outbox Dispatcher started (limit=%s, sleep=%s)",
        settings.OUTBOX_POLL_LIMIT,
        settings.OUTBOX_IDLE_SLEEP,
    )

    svcs = get_services()
    redis_conn = Redis.from_url(settings.REDIS_URL)
    q_outbox = Queue("outbox", connection=redis_conn)

    while True:
        time.sleep(settings.OUTBOX_IDLE_SLEEP)
        try:
            result = svcs.outboxs.enqueue_outbox_pending(settings.OUTBOX_POLL_LIMIT, q_outbox)
            if not result:
                logger.debug(
                    "no pending outbox rows, sleeping %.2fs", settings.OUTBOX_IDLE_SLEEP
                )
                time.sleep(settings.OUTBOX_IDLE_SLEEP)
                continue

        except Exception:
            logger.exception("dispatcher loop error")
            time.sleep(settings.OUTBOX_IDLE_SLEEP)


if __name__ == "__main__":
    main()
