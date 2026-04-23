from app.core.constants import TICKER
from app.infra.external.redis.async_redis_client import RedisClientAsync
from app.domain import MarketPort

class RedisTickerStore(MarketPort.AsyncTickerStore):
    def __init__(
        self,
        redis: RedisClientAsync,
        prefix: str
    ):
        self._redis = redis
        self._prefix = prefix

    async def subscribe(self, interval_type: str):
        pubsub = await self._redis.psubscribe(f"{self._prefix}:{TICKER}:{interval_type}:*")
        return pubsub
