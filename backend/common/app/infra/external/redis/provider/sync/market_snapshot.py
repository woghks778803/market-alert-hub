import json
from app.core.constants import CANDLE, TICKER
from app.domain import MarketPort
from app.infra.external.redis.redis_client import RedisClient


class RedisMarketSnapshot(MarketPort.MarketSnapshot):
    def __init__(self, redis: RedisClient, prefix: str):
        self._redis = redis
        self._prefix = prefix

    def candle_publish(self, payloads: list, interval_type: str) -> None:
        if not payloads:
            return

        for p in payloads:
            key = f"{self._prefix}:{CANDLE}:{interval_type}:{p['exchange_code']}:{p['exchange_symbol']}"
            self._redis.hset(
                key,
                mapping=p,
            )

            self._redis.publish(key, json.dumps(p))

    def ticker_publish(self, payloads: list, interval_type: str) -> None:
        if not payloads:
            return

        for p in payloads:
            key = f"{self._prefix}:{TICKER}:{interval_type}:{p['exchange_code']}:{p['exchange_symbol']}"
            self._redis.hset(
                key,
                mapping=p,
            )

            self._redis.publish(key, json.dumps(p))
