from dataclasses import dataclass
from app.service.sync.factory import ServiceFactory
from app.service.aio.factory import AsyncServiceFactory
from app.core import dto as CoreDTO

from app.infra.external.redis.redis_client import RedisClient
from app.infra.external.redis.async_redis_client import RedisClientAsync

from app.infra.external.exchange.port.ws_client import (
    WsFactoryRegistry,
)
from app.infra.external.exchange.port.subscribe import SubscribeFactoryRegistry


@dataclass(frozen=True)
class WsContext:
    config: CoreDTO.WsConfigBag
    svcs: AsyncServiceFactory


@dataclass(frozen=True)
class ApiContext:
    config: CoreDTO.ApiConfigBag
    svcs: ServiceFactory


@dataclass(frozen=True)
class SchedulerContext:
    config: CoreDTO.SchedulerConfigBag
    svcs: ServiceFactory


@dataclass(frozen=True)
class WorkerContext:
    config: CoreDTO.WorkerConfigBag
    svcs: ServiceFactory
    redis_client: RedisClient


@dataclass(frozen=True)
class DispatcherContext:
    config: CoreDTO.DispatcherConfigBag
    svcs: AsyncServiceFactory


@dataclass(frozen=True)
class CollectorContext:
    config: CoreDTO.CollectorConfigBag
    svcs: AsyncServiceFactory
    subscribe_facs_register: SubscribeFactoryRegistry
    ws_facs_register: WsFactoryRegistry
    async_redis_client: RedisClientAsync


@dataclass(frozen=True)
class StreamProcessorContext:
    config: CoreDTO.StreamProcessorConfigBag
    svcs: AsyncServiceFactory
    async_redis_client: RedisClientAsync
