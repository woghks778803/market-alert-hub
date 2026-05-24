from app.core.constants import TICKER
from app.domain import MarketPort
from app.infra.external.redis.async_redis_client import RedisClientAsync

class RedisTickerStore(MarketPort.AsyncTickerStore):
    def __init__(
        self,
        redis: RedisClientAsync,
        prefix: str
    ):
        self._redis = redis
        self._prefix = prefix

    async def subscribe(self, interval_type: str):
        pubsub = await self._redis.subscribe(f"{self._prefix}:{TICKER}:{interval_type}:UPBIT:KRW-BTC")
        return pubsub
