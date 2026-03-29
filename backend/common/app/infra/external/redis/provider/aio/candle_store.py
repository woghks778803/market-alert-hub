import json
from typing import Callable
from app.core.constants import CANDLE
from app.infra.external.redis.async_redis_client import RedisClientAsync
from app.facade.ports import CandleStore


class RedisCandleStore(CandleStore):
    def __init__(
        self,
        redis: RedisClientAsync,
        *,
        symbols_1s_key_fn: Callable[[str, str], str],
    ):
        self._redis = redis
        self._symbols_1s_key_fn = symbols_1s_key_fn

    async def write_1s(self, state: dict) -> None:
        key = self._symbols_1s_key_fn(state["exchange_code"], state["exchange_symbol"])
        # print("write_1s state", state, key)
        payload = {
            "exchange_code": state["exchange_code"],
            "exchange_symbol": state["exchange_symbol"],
            "open": str(state["open"]),
            "high": str(state["high"]),
            "low": str(state["low"]),
            "close": str(state["close"]),
            "volume": str(state["volume"]),
            "ts_open": state["ts_open"],
        }

        await self._redis.hset(
            key,
            mapping=payload,
        )

        await self._redis.publish(key, json.dumps(payload))

    async def get_1s(self, exchange: str, symbol: str) -> dict | None:
        key = self._symbols_1s_key_fn(exchange, symbol)
        raw = await self._redis.hgetall(key)

        if not raw:
            return None

        return {
            "exchange_code": raw.get(b"exchange_code", b""),
            "exchange_symbol": raw.get(b"exchange_symbol", b""),
            "open": float(raw.get(b"open", 0)),
            "high": float(raw.get(b"high", 0)),
            "low": float(raw.get(b"low", 0)),
            "close": float(raw.get(b"close", 0)),
            "volume": float(raw.get(b"volume", 0)),
            "ts_open": int(raw.get(b"ts_open", 0)),
        }

    async def subscribe(self, type: str):
        pubsub = await self._redis.psubscribe(f"{CANDLE}:{type}:*")
        return pubsub
