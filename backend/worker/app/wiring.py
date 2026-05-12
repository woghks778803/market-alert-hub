from dataclasses import dataclass
from functools import lru_cache

from app.core import dto as CoreDTO
from app.service.sync.factory import ServiceFactory
from app.runtime.app_context import WorkerContext
from app.runtime.bootstrap import create_worker_context


@dataclass(frozen=True)
class WorkerRuntime:
    svcs: ServiceFactory
    config: CoreDTO.WorkerConfigBag


@lru_cache(maxsize=1)
def get_app_context() -> WorkerContext:
    return create_worker_context()


def build_worker_runtime() -> WorkerRuntime:
    ctx = get_app_context()

    return WorkerRuntime(
        svcs=ctx.svcs,
        config=ctx.config,
    )
