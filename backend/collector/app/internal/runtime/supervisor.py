import asyncio
import logging
import random
from collections.abc import Awaitable, Callable, Iterable
from dataclasses import dataclass

logger = logging.getLogger(__name__)

TaskFactory = Callable[[], Awaitable[None]]
OnErrorHook = Callable[[str, BaseException], None]


@dataclass(frozen=True)
class RestartPolicy:
    """
    태스크가 예외로 죽었을 때 재시작 정책.

    - base_backoff_sec: 첫 재시작 대기 시간
    - max_backoff_sec: 최대 대기 시간(지수 백오프 상한)
    - jitter_ratio: 대기 시간에 랜덤 지터를 섞어서(예: 0.2면 ±20%) 동시 재시작 폭주 방지
    """

    base_backoff_sec: float = 2.0
    max_backoff_sec: float = 30.0
    jitter_ratio: float = 0.2

    def next_delay(self, current_delay: float) -> float:
        # 지수 백오프: current_delay가 0이면 base를 쓰고, 아니면 2배(상한 적용)
        if current_delay <= 0:
            delay = self.base_backoff_sec
        else:
            delay = min(self.max_backoff_sec, current_delay * 2)

        # 지터 적용(± jitter_ratio)
        if self.jitter_ratio > 0:
            span = delay * self.jitter_ratio
            delay = max(0.0, delay + random.uniform(-span, span))
        return delay


async def _sleep_or_stop(stop_event: asyncio.Event, seconds: float) -> None:
    """
    seconds 동안 자되, stop_event가 먼저 set되면 즉시 깨어난다.
    """
    if seconds <= 0:
        return
    try:
        await asyncio.wait_for(stop_event.wait(), timeout=seconds)
    except asyncio.TimeoutError:
        return


async def run_with_restart(
    *,
    name: str,
    stop_event: asyncio.Event,
    task_factory: TaskFactory,
    policy: RestartPolicy | None = None,
    on_error: OnErrorHook | None = None,
) -> None:
    """
    task_factory()로 생성한 코루틴을 실행하고,
    예외로 종료되면 restart policy에 따라 재시작한다.

    기대하는 사용 패턴:
    - 태스크(예: WS 스트림 루프)는 내부에서 stop_event를 보고 정상 종료한다.
    - stop_event가 set되면 supervisor도 더 이상 재시작하지 않고 반환한다.
    """
    policy = policy or RestartPolicy()
    delay = 0.0

    while True:
        if stop_event.is_set():
            logger.info("task.stop_requested name=%s", name)
            return

        try:
            logger.info("task.start name=%s", name)
            await task_factory()

            # 태스크가 정상 종료되었다면:
            # - stop_event 때문에 내려간 경우가 흔함
            # - stop_event가 아닌데도 종료되면(=예상치 못한 종료) 재시작하는 편이 안전
            if stop_event.is_set():
                logger.info("task.exit name=%s reason=stop_event", name)
                return

            logger.warning(
                "task.exit name=%s reason=unexpected_return -> restart", name
            )
            delay = policy.base_backoff_sec
            await _sleep_or_stop(stop_event, delay)
            continue

        except asyncio.CancelledError:
            # 상위에서 cancel되면 그대로 전파(정상 동작)
            logger.info("task.cancelled name=%s", name)
            raise

        except Exception as e:
            # 태스크 크래시 → 로깅 후 백오프 재시작
            logger.exception("task.crash name=%s", name)
            if on_error is not None:
                try:
                    on_error(name, e)
                except Exception:
                    logger.exception("on_error hook failed name=%s", name)

            delay = policy.next_delay(delay)
            logger.info("task.restart_scheduled name=%s delay_sec=%.2f", name, delay)
            await _sleep_or_stop(stop_event, delay)


def build_supervised_tasks(
    *,
    stop_event: asyncio.Event,
    specs: Iterable[tuple[str, TaskFactory]],
    policy: RestartPolicy | None = None,
    on_error: OnErrorHook | None = None,
) -> list[asyncio.Task[None]]:
    """
    여러 태스크를 supervisor로 감싸서 asyncio.Task 목록을 만든다.
    run.py에서 gather/cancel에 활용하기 좋게 분리해둔 유틸.
    """
    tasks: list[asyncio.Task[None]] = []
    for name, factory in specs:
        t = asyncio.create_task(
            run_with_restart(
                name=name,
                stop_event=stop_event,
                task_factory=factory,
                policy=policy,
                on_error=on_error,
            ),
            name=f"supervised:{name}",
        )
        tasks.append(t)
    return tasks
