from dataclasses import dataclass
from app.service.factory import ServiceFactory
from redis.client import Redis

@dataclass(frozen=True)
class AppContext:
    svcs: ServiceFactory
    redis_conn: Redis
