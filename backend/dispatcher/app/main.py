import time
import logging
from rq import Queue
from redis import Redis
from app.core.settings import settings
from app.core.logging import setup_logging
from app.deps import get_services

logger = logging.getLogger("dispatcher")


def main() -> None:
    setup_logging()
    logger.info("🚀 Outbox Dispatcher started (limit=%s, sleep=%s)",
                settings.OUTBOX_POLL_LIMIT, settings.OUTBOX_IDLE_SLEEP)

    svcs = get_services()
    redis_conn = Redis.from_url(settings.REDIS_URL)
    q_outbox = Queue("outbox", connection=redis_conn)

    while True:
        try:
            # 1️⃣ PENDING 상태 중 발송 시도 가능한 항목 가져오기
            ids = svcs.outbox().fetch_and_mark_sending(settings.OUTBOX_POLL_LIMIT)
            if not ids:
                logger.debug("no pending outbox rows, sleeping %.2fs", settings.OUTBOX_IDLE_SLEEP)
                time.sleep(settings.OUTBOX_IDLE_SLEEP)
                continue

            # 2️⃣ 각 이벤트를 RQ 큐에 등록
            for event_id in ids:
                q_outbox.enqueue("app.jobs.process_outbox.process_outbox_event", event_id)
                logger.info("enqueued outbox id=%s", event_id)

        except Exception:
            logger.exception("dispatcher loop error")
            time.sleep(settings.OUTBOX_IDLE_SLEEP)


if __name__ == "__main__":
    main()
