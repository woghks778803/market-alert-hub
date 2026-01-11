import logging
import threading
from dataclasses import dataclass
from functools import lru_cache
from typing import Any, Callable
from app.runtime.sync.lifecycle.signals import install_signal_handlers
from app.runtime.sync.supervision.supervisor import (
    RestartPolicy,
    build_supervised_tasks,
)
from app.runtime.sync.state.checkpoint_store import (
    CheckpointStore,
    FileCheckpointStore,
    MemoryCheckpointStore,
)
from app.runtime.bootstrap import create_scheduler_context
from app.runtime.app_context import SchedulerContext
from app.scheduler_loop import run_scheduler_loop
from app.tasks import build_default_tasks

logger = logging.getLogger(__name__)

TaskFactory = Callable[[], Any]  # worker(Thread 등) 또는 runnable 반환(감독자가 해석)


@dataclass
class SchedulerRuntime:
    """
    run.py가 duck-typing으로 기대하는 런타임 타입 묶음.
    stop_event는 run.py에서 생성/바인딩 된다.
    """

    ctx: SchedulerContext
    specs: list[tuple[str, TaskFactory]]
    checkpoint_store: CheckpointStore
    restart_policy: RestartPolicy
    on_task_error: Callable[[str, BaseException], None]
    stop_event: Any | None = None

    def close(self) -> None:
        # run.py에서 best-effort close를 호출하므로, 여기서는 비워둬도 됨.
        return


@lru_cache(maxsize=1)
def get_app_context() -> SchedulerContext:
    return create_scheduler_context()


def build_runtime() -> SchedulerRuntime:
    """
    scheduler 컨테이너 부팅 시 1회 호출되는 wiring.
    settings(ctx.config)에서 필요한 값들을 읽어 checkpoint_store / restart_policy / jobs를 조립한다.
    """
    ctx = get_app_context()
    checkpoint_store = _build_checkpoint_store(ctx)
    restart_policy = _build_restart_policy(ctx)
    on_task_error = _build_on_task_error()

    runtime = SchedulerRuntime(
        ctx=ctx,
        specs=[],
        checkpoint_store=checkpoint_store,
        restart_policy=restart_policy,
        on_task_error=on_task_error,
    )

    runtime.specs = _build_specs(runtime)
    return runtime


def _build_checkpoint_store(ctx: SchedulerContext) -> CheckpointStore:
    """
    운영 안정성/재시작 복구를 위해 redis 권장.
    설정이 애매하면 file/memory로 안전하게 기본값 처리.
    """

    # if backend == "redis":
    #     redis_url = getattr(ctx.config, "checkpoint_redis_url", None)
    #     key_prefix = getattr(ctx.config, "checkpoint_key_prefix", "scheduler:ckpt:")
    #     return RedisCheckpointStore(redis_url=redis_url, key_prefix=key_prefix)

    if ctx.config.checkpoint_backend == "file":
        return FileCheckpointStore(path=ctx.config.checkpoint_file_path)

    return MemoryCheckpointStore()


def _build_restart_policy(ctx: SchedulerContext) -> RestartPolicy:
    base = ctx.config.restart_base_backoff_sec
    max_ = ctx.config.restart_max_backoff_sec
    jitter = ctx.config.restart_jitter_ratio
    return RestartPolicy(
        base_backoff_sec=base, max_backoff_sec=max_, jitter_ratio=jitter
    )


def _build_on_task_error() -> Callable[[str, BaseException], None]:
    def _hook(name: str, exc: BaseException) -> None:
        # errorkit으로 바꾸고 싶으면 scheduler/app/exception_handlers.py 같은 곳에서 교체하면 됨
        logger.exception(
            "scheduler.task_error name=%s exc_type=%s", name, exc.__class__.__name__
        )

    return _hook


def create_tasks(
    runtime: SchedulerRuntime, stop_event: threading.Event
) -> list[threading.Thread] | None:

    install_signal_handlers(stop_event)

    # jobs 쪽에서 stop_event를 참조할 수 있게 바인딩
    setattr(runtime, "stop_event", stop_event)

    specs = getattr(runtime, "specs", None)
    if not specs:
        return None

    restart_policy = getattr(runtime, "restart_policy", None)
    if not isinstance(restart_policy, RestartPolicy):
        restart_policy = RestartPolicy()

    on_task_error = getattr(runtime, "on_task_error", None)

    workers = build_supervised_tasks(
        stop_event=stop_event,
        specs=specs,
        policy=restart_policy,
        on_error=on_task_error,
    )

    return workers


def _build_specs(runtime):
    """
    scheduler 컨테이너 작업 목록

    - 스레드는 1개만 사용 (1초 tick 내부에서 A/B/C 모두 처리)
    - stop_event/ctx는 runtime에 이미 바인딩되어 있어야 한다.
    """

    def scheduler_main():
        tasks = build_default_tasks(runtime.ctx.config)
        run_scheduler_loop(runtime.stop_event, runtime.ctx, tasks)

    return [
        ("scheduler", lambda: scheduler_main()),
    ]
