from dataclasses import dataclass
from functools import lru_cache
from redis.client import Redis as SyncRedis
from rq import Queue

from app.service.factory import ServiceFactory
from app.runtime.app_context import AppContext
from app.runtime.bootstrap import create_app_context, get_core_worker_config_bag

worker_config = get_core_worker_config_bag()

@dataclass(frozen=True)
class WorkerRuntime:
    svcs: ServiceFactory
    redis_conn: SyncRedis
    q_outbox: Queue

@lru_cache(maxsize=1)
def get_app_context() -> AppContext:
    return create_app_context()

def build_worker_runtime() -> WorkerRuntime:
    ctx = get_app_context()
    q_outbox = Queue("outbox", connection=ctx.redis_conn)

    return WorkerRuntime(
        svcs=ctx.svcs,
        redis_conn=ctx.redis_conn,
        q_outbox=q_outbox,
    )
