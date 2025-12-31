from dataclasses import dataclass
from functools import lru_cache

from redis.client import Redis as SyncRedis
from rq import Queue

from app.core import dto as CoreDTO
from app.service.factory import ServiceFactory
from app.runtime.app_context import DispatcherContext
from app.runtime.bootstrap import create_dispatcher_context


@dataclass(frozen=True)
class DispatcherRuntime:
    svcs: ServiceFactory
    config: CoreDTO.DispatcherConfigBag
    redis_conn: SyncRedis
    q_outbox: Queue


@lru_cache(maxsize=1)
def get_app_context() -> DispatcherContext:
    return create_dispatcher_context()


def build_dispatcher_runtime() -> DispatcherRuntime:
    ctx = get_app_context()

    redis_conn = ctx.redis_client.conn()
    q_outbox = Queue("outbox", connection=redis_conn)

    return DispatcherRuntime(
        svcs=ctx.svcs,
        config=ctx.config,
        redis_conn=redis_conn,
        q_outbox=q_outbox,
    )
