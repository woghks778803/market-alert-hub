from typing import Callable
from app.domain import MarketPort
from app.infra.external.redis.redis_client import RedisClient


class RedisCandleStore(MarketPort.CandleStore):
    def __init__(
        self,
        redis: RedisClient,
        *,
        symbols_1s_key_fn: Callable[[str, str], str],
    ):
        self._redis = redis
        self._symbols_1s_key_fn = symbols_1s_key_fn

    def get_1s(self, exchange: str, symbol: str) -> dict | None:
        key = self._symbols_1s_key_fn(exchange, symbol)
        raw = self._redis.hgetall(key)

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
