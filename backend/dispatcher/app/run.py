import logging
import signal
import time

from app.core.logging import setup_logging
from .wiring import build_dispatcher_runtime

log = logging.getLogger("dispatcher")


def run() -> None:
    setup_logging(level=logging.INFO, service="dispatcher")

    rt = build_dispatcher_runtime()
    stop = {"flag": False}

    def _handle_stop(signum, frame):  # noqa: ARG001
        log.warning("dispatcher stopping by signal=%s", signum)
        stop["flag"] = True

    signal.signal(signal.SIGTERM, _handle_stop)
    signal.signal(signal.SIGINT, _handle_stop)

    poll_limit = rt.config.outbox_poll_limit
    idle_sleep = rt.config.outbox_idle_sleep

    log.info("dispatcher started (poll_limit=%s idle_sleep=%s)", poll_limit, idle_sleep)

    while not stop["flag"]:
        try:
            n = rt.svcs.outboxs.enqueue_outbox_pending(poll_limit, rt.q_outbox)
            if not n:
                time.sleep(idle_sleep)
                continue
        except Exception:
            log.exception("dispatcher loop error")
            time.sleep(idle_sleep)

    log.info("dispatcher stopped")
