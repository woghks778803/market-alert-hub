from typing import Callable
from app.core.constants import CANDLE, CandleInterval
from app.domain import MarketPort
from app.infra.external.redis.redis_client import RedisClient


class RedisCandleStore(MarketPort.CandleStore):
    def __init__(
        self,
        redis: RedisClient,
        *,
        prefix: str,
    ):
        self._redis = redis
        self._prefix = prefix

    def get_1s(self, exchange: str, symbol: str) -> dict | None:
        key = self._symbols_1s_key(exchange, symbol)
        raw = self._redis.hgetall(key)

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

    def _symbols_1s_key(self, ex, symbol) -> str:
        return f"{self._prefix}:{CANDLE}:{CandleInterval.SEC_1.value}:{ex}:{symbol}"