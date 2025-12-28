import asyncio
import logging
from typing import Any

from app.internal.runtime.signals import install_signal_handlers
from app.internal.runtime.supervisor import RestartPolicy, build_supervised_tasks

logger = logging.getLogger(__name__)


async def _maybe_await_close(obj: Any) -> None:
    """
    runtime/checkpoint_store/redis client 등이 close() 또는 aclose()를 제공할 수 있어서
    best-effort로 정리한다.
    """
    for name in ("aclose", "close"):
        fn = getattr(obj, name, None)
        if fn is None or not callable(fn):
            continue

        try:
            ret = fn()
            if asyncio.iscoroutine(ret):
                await ret
        except Exception:
            logger.exception("close failed obj=%s fn=%s", obj.__class__.__name__, name)
        return


async def run(runtime: Any) -> None:
    """
    collector 런타임 실행 루프.

    runtime에서 기대하는 최소 속성(duck-typing):
    - runtime.jobs: list[tuple[str, callable]]
        - 각 callable은 '코루틴을 반환하는 팩토리'여야 함 (task_factory: () -> awaitable)
        - 예: [("catalog", make_catalog_task), ("stream", make_stream_task)]
    - (optional) runtime.restart_policy: RestartPolicy
    - (optional) runtime.on_task_error: callable(name: str, exc: BaseException) -> None

    stop_event는 run()에서 생성하고 signals가 set()한다.
    각 job은 stop_event를 직접 받는 방식으로 wiring에서 closure로 캡쳐시키는 걸 권장.
    """
    stop_event = asyncio.Event()
    install_signal_handlers(stop_event)

    jobs = getattr(runtime, "jobs", None)
    if not jobs:
        logger.warning("collector.no_jobs")
        return

    restart_policy = getattr(runtime, "restart_policy", None)
    if not isinstance(restart_policy, RestartPolicy):
        restart_policy = RestartPolicy()

    on_task_error = getattr(runtime, "on_task_error", None)

    tasks = build_supervised_tasks(
        stop_event=stop_event,
        specs=jobs,
        policy=restart_policy,
        on_error=on_task_error,
    )

    logger.info("collector.run tasks=%d", len(tasks))

    try:
        # 정상 종료 신호(SIGTERM/SIGINT)가 오면 stop_event가 set됨
        await stop_event.wait()

    finally:
        # stop 요청 이후에는 태스크 정리
        logger.info("collector.stopping cancel_tasks=%d", len(tasks))
        for t in tasks:
            t.cancel()

        await asyncio.gather(*tasks, return_exceptions=True)

        # runtime이 소유한 리소스 정리(best-effort)
        checkpoint_store = getattr(runtime, "checkpoint_store", None)
        if checkpoint_store is not None:
            await _maybe_await_close(checkpoint_store)

        await _maybe_await_close(runtime)

        logger.info("collector.stopped")
