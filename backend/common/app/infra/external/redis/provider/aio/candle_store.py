import json
from typing import Callable, Sequence

from app.core.constants import CANDLE, CandleInterval
from app.domain import MarketPort
from app.infra.external.redis.async_redis_client import RedisClientAsync

class RedisCandleStore(MarketPort.AsyncCandleStore):
    def __init__(
        self,
        redis: RedisClientAsync,
        *,
        prefix: str,
    ):
        self._redis = redis
        self._prefix = prefix

    async def write_1s(self, state: dict) -> None:
        key = self._symbols_1s_key(state["exchange_code"], state["exchange_symbol"])
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
        key = self._symbols_1s_key(exchange, symbol)
        raw = await self._redis.hgetall(key)

        if not raw:
            return None

        return {
            "exchange_code": raw.get(b"exchange_code", b"").decode(),
            "exchange_symbol": raw.get(b"exchange_symbol", b"").decode(),
            "open": raw.get(b"open", b"0").decode(),
            "high": raw.get(b"high", b"0").decode(),
            "low": raw.get(b"low", b"0").decode(),
            "close": raw.get(b"close", b"0").decode(),
            "volume": raw.get(b"volume", b"0").decode(),
            "ts_open": int(raw.get(b"ts_open", b"0")),
        }

    async def subscribe(self, channels: Sequence[str]):
        if isinstance(channels, str):
            raise TypeError("channels must be a sequence of channel names, not str")

        if not channels:
            raise ValueError("subscribe channels must not be empty")
            
        pubsub = await self._redis.subscribe(*channels)
        return pubsub

    def channel_key(self, interval_type: str, ex: str, symbol: str) -> str:
        return f"{self._prefix}:{CANDLE}:{interval_type}:{ex}:{symbol}"

    def _symbols_1s_key(self, ex, symbol) -> str:
        return f"{self._prefix}:{CANDLE}:{CandleInterval.SEC_1.value}:{ex}:{symbol}"
