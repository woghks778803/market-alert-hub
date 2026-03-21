from dataclasses import dataclass
from app.service.factory import ServiceFactory
from app.core import dto as CoreDTO
from app.infra.external.redis.redis_client import RedisClient
from app.infra.external.redis.async_redis_client import AsyncRedisClient
from app.infra.external.redis.port.active_catalog import ActiveMarketCatalog
from app.infra.external.redis.port.candle_store import CandleStore
from app.infra.external.exchange.port.ws_client import (
    WsFactoryRegistry,
    StreamFactoryRegistry,
)
from app.infra.external.exchange.port.subscribe import SubscribeFactoryRegistry

# @dataclass(frozen=True)
# class AppContext:
#     svcs: ServiceFactory
#     redis_client: RedisClient

#     @property
#     def redis_conn(self) -> SyncRedis:
#         return self.redis_client.conn()


@dataclass(frozen=True)
class WsContext:
    config: CoreDTO.WsConfigBag
    async_redis_client: AsyncRedisClient


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
    subscribe_facs_register: SubscribeFactoryRegistry
    # stream_facs_register: StreamFactoryRegistry
    ws_facs_register: WsFactoryRegistry
    active_catalog: ActiveMarketCatalog
    async_redis_client: AsyncRedisClient


@dataclass(frozen=True)
class StreamProcessorContext:
    config: CoreDTO.StreamProcessorConfigBag
    active_catalog: ActiveMarketCatalog
    candle_store: CandleStore
    async_redis_client: AsyncRedisClient
