import logging
from rq import Worker
from app.core.logging import setup_logging
from .deps import get_redis
from .queues import q_outbox


def run() -> None:
    setup_logging(level=logging.INFO, service="worker")
    # with Connection(get_redis()):
    # 큐 이름 또는 Queue 객체 배열 모두 가능
    redis_conn = get_redis()
    w = Worker([q_outbox], connection=redis_conn)
    w.work(with_scheduler=True)
    # w.work(with_scheduler=True, logging_level=)


# import logging
# from rq import Worker, Connection

# from app.runtime.bootstrap import create_app_context
# from app.core.logging import setup_logging
# from worker.queues import q_outbox

# log = logging.getLogger(__name__)

# def run() -> None:
#     setup_logging(level=logging.INFO, service="worker")

#     ctx = create_app_context()
#     with Connection(ctx.redis_conn):
#         w = Worker([q_outbox])
#         w.work(with_scheduler=True)

if __name__ == "__main__":
    run()
