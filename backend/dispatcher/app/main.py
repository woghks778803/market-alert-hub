import time
import logging
from rq import Queue
from app.core.logging import setup_logging
from app.deps import get_services, get_redis, dispatcher_config

logger = logging.getLogger("dispatcher")


def main() -> None:
    setup_logging()
    logger.info(
        "Outbox Dispatcher started (limit=%s, sleep=%s)",
        dispatcher_config.outbox_poll_limit,
        dispatcher_config.outbox_idle_sleep,
    )

    svcs = get_services()
    redis_conn = get_redis()
    q_outbox = Queue("outbox", connection=redis_conn)

    while True:
        time.sleep(dispatcher_config.outbox_idle_sleep)
        try:
            result = svcs.outboxs.enqueue_outbox_pending(
                dispatcher_config.outbox_poll_limit, q_outbox
            )
            if not result:
                logger.debug(
                    "no pending outbox rows, sleeping %.2fs",
                    dispatcher_config.outbox_idle_sleep,
                )
                time.sleep(dispatcher_config.outbox_idle_sleep)
                continue

        except Exception:
            logger.exception("dispatcher loop error")
            time.sleep(dispatcher_config.outbox_idle_sleep)


if __name__ == "__main__":
    main()
