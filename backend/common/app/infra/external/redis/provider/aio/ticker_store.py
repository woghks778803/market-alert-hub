from typing import Sequence

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

    async def subscribe(self, channels: Sequence[str]):
        pubsub = await self._redis.subscribe(*channels)
        return pubsub

    def channel_key(self, interval_type: str, ex: str, symbol: str) -> str:
        return f"{self._prefix}:{TICKER}:{interval_type}:{ex}:{symbol}"