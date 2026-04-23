from dataclasses import dataclass
from functools import lru_cache
from redis.client import Redis as SyncRedis
from rq import Queue
from app.core import dto as CoreDTO
from app.service.sync.factory import ServiceFactory
from app.runtime.app_context import WorkerContext
from app.runtime.bootstrap import create_worker_context


@dataclass(frozen=True)
class WorkerRuntime:
    svcs: ServiceFactory
    config: CoreDTO.WorkerConfigBag
    redis_conn: SyncRedis
    q_outbox: Queue


@lru_cache(maxsize=1)
def get_app_context() -> WorkerContext:
    return create_worker_context()


def build_worker_runtime() -> WorkerRuntime:
    ctx = get_app_context()

    redis_conn = ctx.redis_client.conn()
    q_outbox = Queue("outbox", connection=redis_conn)

    return WorkerRuntime(
        svcs=ctx.svcs,
        config=ctx.config,
        redis_conn=redis_conn,
        q_outbox=q_outbox,
    )
