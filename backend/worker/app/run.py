import logging
import signal
from rq import Worker

from app.core.logging import setup_logging
from .wiring import build_worker_runtime

log = logging.getLogger("worker")


def run() -> None:
    setup_logging(level=logging.INFO, service="worker")

    rt = build_worker_runtime()

    worker = Worker([rt.q_outbox], connection=rt.redis_conn)

    # SIGTERM 받으면 현재 job 끝내고 종료
    def _handle_stop(signum, frame):  # noqa: ARG001
        log.warning("worker stopping by signal=%s", signum)
        try:
            worker.request_stop(signum=signum, frame=frame)
        except Exception:
            log.exception("failed to request_stop")

    signal.signal(signal.SIGTERM, _handle_stop)
    signal.signal(signal.SIGINT, _handle_stop)

    worker.work(with_scheduler=True)
