import logging
import threading
import time
from typing import Any
from app.wiring import create_tasks

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


def run(runtime: Any) -> None:
    """
    scheduler 컨테이너 실행 루프.

    runtime에서 기대하는 최소 속성(duck-typing):
      - runtime.jobs: list[tuple[str, callable]]  # (name, task_factory)
        task_factory() -> worker (Thread 또는 join 가능한 오브젝트)
      - (optional) runtime.restart_policy: RestartPolicy
      - (optional) runtime.on_task_error: callable(name: str, exc: BaseException) -> None

    stop_event는 run()에서 생성 후 signals 설치하고 runtime.stop_event로 바인딩.
    """
    stop_event = threading.Event()

    workers = create_tasks(runtime, stop_event)
    if not workers:
        logger.warning("scheduler.no_jobs")
        return

    logger.info("scheduler.run workers=%d", len(workers))
    try:
        while not stop_event.is_set():
            time.sleep(0.2)

    finally:
        logger.info("scheduler.stopping join_workers=%d", len(workers))
        for w in workers:
            try:
                join = getattr(w, "join", None)
                if callable(join):
                    join(timeout=5.0)
            except Exception:
                logger.exception("scheduler.worker_join_failed")

        checkpoint_store = getattr(runtime, "checkpoint_store", None)
        if checkpoint_store is not None:
            _maybe_close(checkpoint_store)

        _maybe_close(runtime)
        logger.info("scheduler.stopped")
