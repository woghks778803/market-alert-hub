from dataclasses import dataclass
from app.service.factory import ServiceFactory
from app.core import dto as CoreDTO
from app.infra.external.redis.redis_client import RedisClient
from app.infra.external.redis.async_redis_client import AsyncRedisClient


# @dataclass(frozen=True)
# class AppContext:
#     svcs: ServiceFactory
#     redis_client: RedisClient

#     @property
#     def redis_conn(self) -> SyncRedis:
#         return self.redis_client.conn()


@dataclass(frozen=True)
class ApiContext:
    config: CoreDTO.ApiConfigBag
    svcs: ServiceFactory


@dataclass(frozen=True)
class SchedulerContext:
    config: CoreDTO.SchedulerConfigBag
    svcs: ServiceFactory
    redis_client: RedisClient


@dataclass(frozen=True)
class DispatcherContext:
    config: CoreDTO.DispatcherConfigBag
    svcs: ServiceFactory
    redis_client: RedisClient


@dataclass(frozen=True)
class WorkerContext:
    config: CoreDTO.WorkerConfigBag
    svcs: ServiceFactory
    redis_client: RedisClient


@dataclass(frozen=True)
class CollectorContext:
    config: CoreDTO.CollectorConfigBag
    async_redis_client: AsyncRedisClient
