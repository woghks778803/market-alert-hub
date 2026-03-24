import json
from app.core.constants import CANDLE
from app.domain import MarketPort
from app.infra.external.redis.redis_client import RedisClient


class RedisMarketSnapshotPublish(MarketPort.MarketSnapshotPublish):
    def __init__(self, redis: RedisClient):
        self._redis = redis

    def publish(self, payloads: list, type: str) -> None:
        if not payloads:
            return
        pipe = self._redis.pipeline()

        for p in payloads:
            key = f"{CANDLE}:{type}:{p['exchange_code']}:{p['exchange_symbol']}"
            pipe.hset(
                key,
                mapping=p,
            )

            pipe.publish(key, json.dumps(p))

        pipe.execute()
