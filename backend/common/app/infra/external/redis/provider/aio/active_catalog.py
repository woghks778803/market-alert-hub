import json
from typing import Any, Callable, Mapping
from app.infra.external.redis.async_redis_client import RedisClientAsync
from app.facade.ports import ActiveMarketCatalog, JsonDict


def _to_str(v: Any) -> str:
    if v is None:
        return ""
    if isinstance(v, bytes):
        return v.decode("utf-8", errors="replace")
    return str(v)


def _loads_json(v: Any) -> JsonDict:
    """
    redis hash value (bytes/str) -> dict
    - 값이 비어있거나 파싱 실패하면 {} 반환
    """
    s = _to_str(v).strip()
    if not s:
        return {}
    try:
        obj = json.loads(s)
        return obj if isinstance(obj, dict) else {}
    except Exception:
        return {}


class RedisActiveMarketCatalog(ActiveMarketCatalog):
    """
    Redis 스냅샷(HASH field -> json payload)을 그대로 읽어온다.
    - snap 키: hgetall()로 전체 (field + payload)
    - meta 키: hgetall()로 전체 (started_at, count 등)
    """

    def __init__(
        self,
        redis: RedisClientAsync,
        *,
        exchanges_snap_key: str,
        exchanges_meta_key: str,
        symbols_snap_key_fn: Callable[[str], str],
        symbols_meta_key_fn: Callable[[str], str],
    ) -> None:
        self._redis = redis
        self._ex_snap_key = exchanges_snap_key
        self._ex_meta_key = exchanges_meta_key
        self._sym_snap_key_fn = symbols_snap_key_fn
        self._sym_meta_key_fn = symbols_meta_key_fn

    async def get_exchanges_snap(self) -> Mapping[str, JsonDict]:
        raw: dict[Any, Any] = await self._redis.hgetall(self._ex_snap_key) or {}
        # field: exchange_code, value: json
        return {_to_str(k): _loads_json(v) for k, v in raw.items() if k}

    async def get_exchanges_meta(self) -> Mapping[str, str]:
        raw: dict[Any, Any] = await self._redis.hgetall(self._ex_meta_key) or {}
        return {_to_str(k): _to_str(v) for k, v in raw.items() if k}

    async def get_symbols_snap(self, exchange_code: str) -> Mapping[str, JsonDict]:
        key = self._sym_snap_key_fn(exchange_code)
        raw: dict[Any, Any] = await self._redis.hgetall(key) or {}
        # field: exchange_symbol, value: json
        return {_to_str(k): _loads_json(v) for k, v in raw.items() if k}

    async def get_symbols_meta(self, exchange_code: str) -> Mapping[str, str]:
        key = self._sym_meta_key_fn(exchange_code)
        raw: dict[Any, Any] = await self._redis.hgetall(key) or {}
        return {_to_str(k): _to_str(v) for k, v in raw.items() if k}
