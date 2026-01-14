import logging
import asyncio
from dataclasses import dataclass
from functools import lru_cache
from typing import Any, Callable
from app.runtime.aio.lifecycle.signals import install_signal_handlers
from app.runtime.aio.supervision.supervisor import RestartPolicy, build_supervised_tasks
from app.runtime.aio.state.checkpoint_store import (
    CheckpointStore,
    FileCheckpointStore,
    MemoryCheckpointStore,
)
from app.runtime.bootstrap import create_collector_context
from app.runtime.app_context import CollectorContext

logger = logging.getLogger(__name__)
TaskFactory = Callable[[], Any]


@dataclass
class CollectorRuntime:
    """
    run.py가 duck-typing으로 기대하는 런타임 묶음.

    주의: stop_event는 run.py에서 생성되므로 여기서는 None으로 시작하고,
    run.py에서 runtime.stop_event = stop_event 로 바인딩해서 jobs가 공유하도록 한다.
    """

    ctx: CollectorContext
    specs: list[tuple[str, TaskFactory]]
    checkpoint_store: CheckpointStore
    restart_policy: RestartPolicy
    on_task_error: Callable[[str, BaseException], None]
    stop_event: Any | None = None  # asyncio.Event가 들어올 예정

    def close(self) -> None:
        # run.py에서 aclose/close를 best-effort로 호출하므로 여기서는 비워둬도 됨.
        return


@lru_cache(maxsize=1)
def get_app_context() -> CollectorContext:
    return create_collector_context()


def build_runtime() -> CollectorRuntime:
    """
    collector 컨테이너 부팅 시 호출되는 wiring.
    - settings(공통)에서 필요한 값들을 읽어
    - checkpoint_store / restart_policy / jobs를 조립한다.

    실제 비즈니스 의존성(거래소 클라이언트, repo/uow 등)은
    추후 jobs 구현 단계에서 여기로 주입해 확장하면 된다.
    """
    ctx = get_app_context()
    checkpoint_store = _build_checkpoint_store(ctx)
    restart_policy = _build_restart_policy(ctx)
    on_task_error = _build_on_task_error()

    runtime = CollectorRuntime(
        ctx=ctx,
        specs=[],
        checkpoint_store=checkpoint_store,
        restart_policy=restart_policy,
        on_task_error=on_task_error,
    )

    # jobs는 runtime.stop_event를 참조할 수 있게 "runtime 캡쳐" 형태로 만든다.
    runtime.specs = _build_specs(runtime)

    return runtime


def _build_checkpoint_store(ctx: CollectorContext) -> CheckpointStore:

    # if collector_config.checkpoint_backend == "redis":
    #     redis_url = ctx.config.redis_url
    #     key_prefix = ctx.config.checkpoint_key_prefix
    #     return RedisCheckpointStore(redis_url=redis_url, key_prefix=key_prefix)

    if ctx.config.checkpoint_backend == "file":
        return FileCheckpointStore(path=ctx.config.checkpoint_file_path)

    # default: memory
    return MemoryCheckpointStore()


def _build_restart_policy(ctx: CollectorContext) -> RestartPolicy:
    base = ctx.config.restart_base_backoff_sec
    max_ = ctx.config.restart_max_backoff_sec
    jitter = ctx.config.restart_jitter_ratio
    return RestartPolicy(
        base_backoff_sec=base, max_backoff_sec=max_, jitter_ratio=jitter
    )


def _build_on_task_error() -> Callable[[str, BaseException], None]:
    def _hook(name: str, exc: BaseException) -> None:
        # 여기서 errorkit 연동하고 싶으면(이벤트명 TaskException),
        # collector/app/exception_handlers.py 쪽으로 위임하도록 바꾸면 됨.
        logger.exception(
            "collector.task_error name=%s exc_type=%s", name, exc.__class__.__name__
        )

    return _hook


def _build_specs(runtime: CollectorRuntime) -> list[tuple[str, TaskFactory]]:
    """
    run.py가 stop_event를 만든 뒤 runtime.stop_event에 바인딩하면,
    여기서 만든 task_factory들이 그 stop_event를 공유하게 된다.

    각 task_factory는 '코루틴'을 반환해야 한다.
    """
    from app.stream_marketdata import run_stream_marketdata_loop

    # enable_catalog = runtime.ctx.config.enable_catalog_sync
    # catalog_interval = runtime.ctx.config.catalog_sync_interval_sec

    enable_stream = runtime.ctx.config.enable_stream
    stream_reconnect_backoff = runtime.ctx.config.stream_reconnect_backoff_sec
    specs: list[tuple[str, TaskFactory]] = []

    if enable_stream:

        def stream_factory() -> Any:
            if runtime.stop_event is None:
                raise RuntimeError(
                    "runtime.stop_event is not bound (run.py should set it before starting tasks)"
                )
            return run_stream_marketdata_loop(
                stop_event=runtime.stop_event,
                checkpoint_store=runtime.checkpoint_store,
                reconnect_backoff_sec=stream_reconnect_backoff,
            )

        specs.append(("market_stream", stream_factory))

    return specs


def create_tasks(
    runtime: CollectorRuntime, stop_event: asyncio.Event
) -> list[asyncio.Task[None]] | None:
    """
    runtime에서 specs/policy/on_task_error를 꺼내 supervised task들을 조립한다.
    """
    # specs 쪽에서 stop_event를 참조할 수 있게 바인딩
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
