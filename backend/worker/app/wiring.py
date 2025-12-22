from dataclasses import dataclass

from redis.client import Redis as SyncRedis
from rq import Queue

from .deps import get_services


@dataclass(frozen=True)
class WorkerRuntime:
    svcs: object
    redis_conn: SyncRedis
    q_outbox: Queue


def build_worker_runtime() -> WorkerRuntime:
    svcs = get_services()

    redis_client = svcs.redis
    redis_conn = redis_client.conn()

    q_outbox = Queue("outbox", connection=redis_conn)

    return WorkerRuntime(
        svcs=svcs,
        redis_conn=redis_conn,
        q_outbox=q_outbox,
    )
