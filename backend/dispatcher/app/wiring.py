from dataclasses import dataclass

from redis.client import Redis as SyncRedis
from rq import Queue

from app.runtime.bootstrap import create_app_context, get_core_dispatcher_config_bag
from app.service.factory import ServiceFactory

dispatcher_config = get_core_dispatcher_config_bag()


@dataclass(frozen=True)
class DispatcherRuntime:
    svcs: ServiceFactory
    redis_conn: SyncRedis
    q_outbox: Queue


def build_dispatcher_runtime() -> DispatcherRuntime:
    ctx = create_app_context()
    q_outbox = Queue("outbox", connection=ctx.redis_conn)
    return DispatcherRuntime(
        svcs=ctx.svcs, redis_conn=ctx.redis_conn, q_outbox=q_outbox
    )
