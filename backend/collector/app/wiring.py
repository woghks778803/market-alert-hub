# collector/app/wiring.py
import logging
from dataclasses import dataclass
from typing import Any, Callable

from app.internal.runtime.supervisor import RestartPolicy
from app.internal.state.checkpoint_store import (
    CheckpointStore,
    FileCheckpointStore,
    MemoryCheckpointStore,
    RedisCheckpointStore,
)
from app.runtime.bootstrap import get_core_collector_config_bag

collector_config = get_core_collector_config_bag()

logger = logging.getLogger(__name__)

TaskFactory = Callable[[], Any]  # () -> Awaitable[None]  (타이핑은 느슨하게 유지)


@dataclass
class CollectorRuntime:
    """
    run.py가 duck-typing으로 기대하는 런타임 묶음.

    주의: stop_event는 run.py에서 생성되므로 여기서는 None으로 시작하고,
    run.py에서 runtime.stop_event = stop_event 로 바인딩해서 jobs가 공유하도록 한다.
    """

    jobs: list[tuple[str, TaskFactory]]
    checkpoint_store: CheckpointStore
    restart_policy: RestartPolicy
    on_task_error: Callable[[str, BaseException], None]
    stop_event: Any | None = None  # asyncio.Event가 들어올 예정

    def close(self) -> None:
        # run.py에서 aclose/close를 best-effort로 호출하므로 여기서는 비워둬도 됨.
        return


def build_runtime() -> CollectorRuntime:
    """
    collector 컨테이너 부팅 시 호출되는 wiring.
    - settings(공통)에서 필요한 값들을 읽어
    - checkpoint_store / restart_policy / jobs를 조립한다.

    실제 비즈니스 의존성(거래소 클라이언트, repo/uow 등)은
    추후 jobs 구현 단계에서 여기로 주입해 확장하면 된다.
    """
    checkpoint_store = _build_checkpoint_store()
    restart_policy = _build_restart_policy()
    on_task_error = _build_on_task_error()

    runtime = CollectorRuntime(
        jobs=[],
        checkpoint_store=checkpoint_store,
        restart_policy=restart_policy,
        on_task_error=on_task_error,
    )

    # jobs는 runtime.stop_event를 참조할 수 있게 "runtime 캡쳐" 형태로 만든다.
    runtime.jobs = _build_jobs(runtime)

    return runtime


def _build_checkpoint_store() -> CheckpointStore:
    """
    기본은 운영 안정성/확장성을 위해 redis가 좋지만,
    현재 settings에 collector 전용 값이 없을 수 있으니 안전하게 기본값을 둔다.
    """

    if collector_config.checkpoint_backend == "redis":
        redis_url = collector_config.redis_url
        key_prefix = collector_config.checkpoint_key_prefix
        return RedisCheckpointStore(redis_url=redis_url, key_prefix=key_prefix)

    if collector_config.checkpoint_backend == "file":
        return FileCheckpointStore(path=collector_config.checkpoint_file_path)

    # default: memory
    return MemoryCheckpointStore()


def _build_restart_policy() -> RestartPolicy:
    base = collector_config.restart_base_backoff_sec
    max_ = collector_config.restart_max_backoff_sec
    jitter = collector_config.restart_jitter_ratio
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


def _build_jobs(runtime: CollectorRuntime) -> list[tuple[str, TaskFactory]]:
    """
    run.py가 stop_event를 만든 뒤 runtime.stop_event에 바인딩하면,
    여기서 만든 task_factory들이 그 stop_event를 공유하게 된다.

    각 task_factory는 '코루틴'을 반환해야 한다.
    """
    # from app.jobs.sync_instruments import run_sync_instruments_loop
    # from app.jobs.stream_marketdata import run_stream_marketdata_loop

    enable_catalog = collector_config.enable_catalog_sync
    enable_stream = collector_config.enable_stream

    catalog_interval = collector_config.catalog_sync_interval_sec
    stream_reconnect_backoff = collector_config.stream_reconnect_backoff_sec
    jobs: list[tuple[str, TaskFactory]] = []

    # if enable_catalog:

    #     def catalog_factory() -> Any:
    #         if runtime.stop_event is None:
    #             raise RuntimeError(
    #                 "runtime.stop_event is not bound (run.py should set it before starting tasks)"
    #             )
    #         return run_sync_instruments_loop(
    #             stop_event=runtime.stop_event,
    #             checkpoint_store=runtime.checkpoint_store,
    #             interval_sec=catalog_interval,
    #             # 실제 거래소/DB 의존성은 이후 단계에서 주입
    #         )

    #     jobs.append(("catalog_sync", catalog_factory))

    # if enable_stream:

    #     def stream_factory() -> Any:
    #         if runtime.stop_event is None:
    #             raise RuntimeError(
    #                 "runtime.stop_event is not bound (run.py should set it before starting tasks)"
    #             )
    #         return run_stream_marketdata_loop(
    #             stop_event=runtime.stop_event,
    #             checkpoint_store=runtime.checkpoint_store,
    #             reconnect_backoff_sec=stream_reconnect_backoff,
    #             # 실제 거래소/DB 의존성은 이후 단계에서 주입
    #         )

    #     jobs.append(("market_stream", stream_factory))

    return jobs
