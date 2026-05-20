import asyncio
import logging
from typing import Any
from app.wiring import StreamProcessorRuntime, create_tasks


logger = logging.getLogger(__name__)


async def _maybe_await_close(obj: Any) -> None:
    """
    비동기 컨테이너용 best-effort close
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


async def run(runtime: StreamProcessorRuntime) -> None:
    """
    stream processor 런타임 실행 루프.
    """
    stop_event = asyncio.Event()
    tasks = create_tasks(runtime, stop_event)
    if not tasks:
        logger.warning("stream processor.no_tasks")
        return

    logger.info("stream processor.run tasks=%d", len(tasks))

    try:
        # 정상 종료 신호(SIGTERM/SIGINT)가 오면 stop_event가 set됨
        await stop_event.wait()

    finally:
        # stop 요청 이후에는 태스크 정리
        logger.info("stream processor.stopping cancel_tasks=%d", len(tasks))
        for t in tasks:
            t.cancel()

        await asyncio.gather(*tasks, return_exceptions=True)

        # runtime이 소유한 리소스 정리(best-effort)
        if runtime.checkpoint_store is not None:
            await _maybe_await_close(runtime.checkpoint_store)

        await _maybe_await_close(runtime)

        logger.info("stream processor.stopped")
