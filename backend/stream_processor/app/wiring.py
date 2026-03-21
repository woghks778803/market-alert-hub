import logging
import asyncio
from dataclasses import dataclass
from functools import lru_cache
from typing import Any, Callable
from app.core.constants import CURSOR
from app.runtime.aio.lifecycle.signals import install_signal_handlers
from app.runtime.aio.supervision.supervisor import RestartPolicy, build_supervised_tasks
from app.runtime.aio.state.checkpoint_store import (
    CheckpointStore,
    FileCheckpointStore,
    MemoryCheckpointStore,
)
from app.runtime.bootstrap import create_stream_processor_context
from app.runtime.app_context import StreamProcessorContext

logger = logging.getLogger(__name__)
TaskFactory = Callable[[], Any]


@dataclass
class StreamProcessorRuntime:
    """
    run.py가 duck-typing으로 기대하는 런타임 묶음.

    주의: stop_event는 run.py에서 생성되므로 여기서는 None으로 시작하고,
    run.py에서 runtime.stop_event = stop_event 로 바인딩해서 jobs가 공유하도록 한다.
    """

    ctx: StreamProcessorContext
    specs: list[tuple[str, TaskFactory]]
    checkpoint_store: CheckpointStore
    restart_policy: RestartPolicy
    on_task_error: Callable[[str, BaseException], None]
    stop_event: Any | None = None  # asyncio.Event가 들어올 예정

    def close(self) -> None:
        # run.py에서 aclose/close를 best-effort로 호출하므로 여기서는 비워둬도 됨.
        return


@lru_cache(maxsize=1)
def get_app_context() -> StreamProcessorContext:
    return create_stream_processor_context()


def build_runtime() -> StreamProcessorRuntime:
    ctx = get_app_context()
    checkpoint_store = _build_checkpoint_store(ctx)
    restart_policy = _build_restart_policy(ctx)
    on_task_error = _build_on_task_error()

    runtime = StreamProcessorRuntime(
        ctx=ctx,
        specs=[],
        checkpoint_store=checkpoint_store,
        restart_policy=restart_policy,
        on_task_error=on_task_error,
    )

    # jobs는 runtime.stop_event를 참조할 수 있게 "runtime 캡쳐" 형태로 만든다.
    runtime.specs = _build_specs(runtime)

    return runtime


def _build_checkpoint_store(ctx: StreamProcessorContext) -> CheckpointStore:

    if ctx.config.checkpoint_backend == "file":
        return FileCheckpointStore(path=ctx.config.checkpoint_file_path)

    # default: memory
    return MemoryCheckpointStore()


def _build_restart_policy(ctx: StreamProcessorContext) -> RestartPolicy:
    base = ctx.config.restart_base_backoff_sec
    max_ = ctx.config.restart_max_backoff_sec
    jitter = ctx.config.restart_jitter_ratio
    return RestartPolicy(
        base_backoff_sec=base, max_backoff_sec=max_, jitter_ratio=jitter
    )


def _build_on_task_error() -> Callable[[str, BaseException], None]:
    def _hook(name: str, exc: BaseException) -> None:
        logger.exception(
            "stream processor.task_error name=%s exc_type=%s",
            name,
            exc.__class__.__name__,
        )

    return _hook


def _build_specs(runtime: Any) -> list[tuple[str, TaskFactory]]:
    from app.stream.ticker_1s import run_ticker_1s_loop

    cfg = runtime.ctx.config
    specs: list[tuple[str, TaskFactory]] = []

    if not cfg.enable_stream:
        return specs

    def _ticker_1s():
        return run_ticker_1s_loop(
            stop_event=runtime.stop_event,
            ctx=runtime.ctx,
        )

    specs.append(("ticker:1s", _ticker_1s))

    return specs


def create_tasks(
    runtime: StreamProcessorRuntime, stop_event: asyncio.Event
) -> list[asyncio.Task[None]] | None:
    install_signal_handlers(stop_event)
    runtime.stop_event = stop_event

    specs = runtime.specs
    if not specs:
        return None

    restart_policy = runtime.restart_policy
    if not isinstance(restart_policy, RestartPolicy):
        restart_policy = RestartPolicy()

    on_task_error = runtime.on_task_error

    return build_supervised_tasks(
        stop_event=stop_event,
        specs=specs,
        policy=restart_policy,
        on_error=on_task_error,
    )
