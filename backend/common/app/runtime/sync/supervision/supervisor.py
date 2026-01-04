import logging
import random
import threading
from collections.abc import Callable, Iterable
from dataclasses import dataclass

logger = logging.getLogger(__name__)

TaskFactory = Callable[[], None]
OnErrorHook = Callable[[str, BaseException], None]


@dataclass(frozen=True)
class RestartPolicy:
    """
    태스크가 예외로 죽었을 때 재시작 정책.

    - base_backoff_sec: 첫 재시작 대기
    - max_backoff_sec: 최대 대기(지수 백오프 상한)
    - jitter_ratio: 지터 비율(예: 0.2면 ±20%) — 동시에 재시작 폭주 방지
    """

    base_backoff_sec: float = 2.0
    max_backoff_sec: float = 30.0
    jitter_ratio: float = 0.2

    def next_delay(self, current_delay: float) -> float:
        # 지수 백오프
        if current_delay <= 0:
            delay = self.base_backoff_sec
        else:
            delay = min(self.max_backoff_sec, current_delay * 2.0)

        # 지터 적용
        if self.jitter_ratio > 0:
            span = delay * self.jitter_ratio
            delay = max(0.0, delay + random.uniform(-span, span))

        return delay


def sleep_or_stop(stop_event: threading.Event, seconds: float) -> None:
    """
    seconds 동안 대기하되 stop_event가 먼저 set되면 즉시 깨어난다.
    """
    if seconds <= 0:
        return
    stop_event.wait(timeout=seconds)


def run_with_restart(
    *,
    name: str,
    stop_event: threading.Event,
    task_factory: TaskFactory,
    policy: RestartPolicy | None = None,
    on_error: OnErrorHook | None = None,
) -> None:
    """
    task_factory()를 실행하고, 예외 종료 시 restart policy에 따라 재시작한다.

    기대되는 사용 패턴:
    - 실제 작업 함수(루프)는 내부에서 stop_event를 보고 정상 종료한다.
    - stop_event가 set되면 supervisor는 더 이상 재시작하지 않고 반환한다.
    """
    policy = policy or RestartPolicy()
    delay = 0.0

    while True:
        if stop_event.is_set():
            logger.info("task_stop_requested name=%s", name)
            return

        try:
            logger.info("task_start name=%s", name)
            task_factory()

            # 정상 종료인데 stop_event가 아니라면 "예상치 못한 return" → 재시작이 안전
            if stop_event.is_set():
                logger.info("task_exit name=%s reason=stop_event", name)
                return

            logger.warning(
                "task_exit name=%s reason=unexpected_return -> restart", name
            )
            delay = policy.base_backoff_sec
            sleep_or_stop(stop_event, delay)
            continue

        except BaseException as e:
            # KeyboardInterrupt/SystemExit도 여기로 들어오지만, 스레드 환경에선 보통 메인에서 처리됨
            logger.exception("task_crash name=%s", name)
            if on_error is not None:
                try:
                    on_error(name, e)
                except Exception:
                    logger.exception("on_error hook failed name=%s", name)

            if stop_event.is_set():
                logger.info("task_exit name=%s reason=stop_event_after_error", name)
                return

            delay = policy.next_delay(delay)
            logger.info("task_restart_scheduled name=%s delay_sec=%.2f", name, delay)
            sleep_or_stop(stop_event, delay)


def build_supervised_workers(
    *,
    stop_event: threading.Event,
    specs: Iterable[tuple[str, TaskFactory]],
    policy: RestartPolicy | None = None,
    on_error: OnErrorHook | None = None,
    daemon: bool = True,
) -> list[threading.Thread]:
    """
    여러 작업을 각각 "감독 스레드"로 실행한다.

    - collector의 asyncio Task 대신, scheduler에서는 thread로 동시 실행을 만든다.
    - 반환값은 시작된 thread 리스트.
    """
    threads: list[threading.Thread] = []
    for name, factory in specs:
        t = threading.Thread(
            target=run_with_restart,
            kwargs={
                "name": name,
                "stop_event": stop_event,
                "task_factory": factory,
                "policy": policy,
                "on_error": on_error,
            },
            name=f"supervised:{name}",
            daemon=daemon,
        )
        t.start()
        threads.append(t)

    return threads
