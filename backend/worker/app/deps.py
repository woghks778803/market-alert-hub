from app.runtime.bootstrap import get_core_services, get_core_worker_config_bag
from app.service.factory import ServiceFactory

from redis import Redis

_redis: Redis | None = None
worker_config = get_core_worker_config_bag()


def get_redis() -> Redis:
    global _redis
    if _redis is None:
        _redis = Redis.from_url(worker_config.redis_url)
    return _redis


def get_services() -> ServiceFactory:
    svcs = get_core_services()
    return svcs
