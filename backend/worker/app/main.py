import logging
from rq import Worker, Connection
from app.core.logging import setup_logging
from app.runtime.settings import settings
from .redis_conn import get_redis
from .queues import q_outbox

def run() -> None:
    setup_logging(level=logging.INFO, service="worker")
    with Connection(get_redis()):
        # 큐 이름 또는 Queue 객체 배열 모두 가능
        w = Worker([q_outbox])
        w.work(with_scheduler=True, logging_level=settings.LOG_LEVEL)

if __name__ == "__main__":
    run()
