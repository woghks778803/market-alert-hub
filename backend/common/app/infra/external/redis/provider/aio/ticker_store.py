from app.core.constants import TICKER
from app.infra.external.redis.async_redis_client import RedisClientAsync
from app.facade.ports import TickerStore


class RedisTickerStore(TickerStore):
    def __init__(
        self,
        redis: RedisClientAsync,
    ):
        self._redis = redis

    async def subscribe(self, type: str):
        pubsub = await self._redis.psubscribe(f"{TICKER}:{type}:*")
        return pubsub
