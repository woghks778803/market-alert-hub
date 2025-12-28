from dataclasses import dataclass
from app.service.factory import ServiceFactory

# TODO: RQ Queue/Worker가 redis-py connection object를 요구해서 타입 힌트를 위해 runtime에 남김
from app.infra.external.redis.redis_client import RedisClient
from app.infra.external.redis.async_redis_client import AsyncRedisClient


@dataclass(frozen=True)
class AppContext:
    svcs: ServiceFactory
    redis_client: RedisClient


@dataclass(frozen=True)
class CollectorContext:
    svcs: ServiceFactory
    async_redis_client: AsyncRedisClient
