from dataclasses import dataclass
from functools import lru_cache

from app.core import dto as CoreDTO
from app.service.aio.factory import AsyncServiceFactory
from app.runtime.app_context import DispatcherContext
from app.runtime.bootstrap import create_dispatcher_context


@dataclass(frozen=True)
class DispatcherRuntime:
    svcs: AsyncServiceFactory
    config: CoreDTO.DispatcherConfigBag


@lru_cache(maxsize=1)
def get_app_context() -> DispatcherContext:
    return create_dispatcher_context()


def build_dispatcher_runtime() -> DispatcherRuntime:
    ctx = get_app_context()

    return DispatcherRuntime(
        svcs=ctx.svcs,
        config=ctx.config,
    )
