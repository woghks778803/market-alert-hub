import logging
import threading
import time
from typing import Any
from app.wiring import SchedulerRuntime, create_tasks

logger = logging.getLogger(__name__)


def _maybe_close(obj: Any) -> None:
    """
    동기 컨테이너용 best-effort close.
    """
    fn = getattr(obj, "close", None)
    if fn is None or not callable(fn):
        return

    try:
        fn()
    except Exception:
        logger.exception("close failed obj=%s", obj.__class__.__name__)


def run(runtime: SchedulerRuntime) -> None:
    """
    scheduler 컨테이너 실행 루프.
    """
    stop_event = threading.Event()

    tasks = create_tasks(runtime, stop_event)
    if not tasks:
        logger.warning("scheduler.no_tasks")
        return

    logger.info("scheduler.run tasks=%d", len(tasks))
    try:
        while not stop_event.is_set():
            time.sleep(0.2)

    finally:
        logger.info("scheduler.stopping join_tasks=%d", len(tasks))
        for t in tasks:
            try:
                join = getattr(t, "join", None)
                if callable(join):
                    join(timeout=5.0)
            except Exception:
                logger.exception("scheduler.worker_join_failed")

        if runtime.checkpoint_store is not None:
            _maybe_close(runtime.checkpoint_store)

        _maybe_close(runtime)
        logger.info("scheduler.stopped")
