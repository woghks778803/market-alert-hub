import uuid
from typing import Any, Mapping, Protocol, runtime_checkable

from app.domain.shared.errors import ValidationAppError


@runtime_checkable
class RedisClientLike(Protocol):
    """
    worker jobs 레벨에서 필요한 최소 API.
    - redis-py(외부 라이브러리) 타입을 여기로 끌고 오지 않기 위한 목적.
    """

    def set(
        self,
        key: str,
        value: bytes,
        *,
        nx: bool = False,
        ex: int | None = None,
    ) -> bool: ...

    def ttl(self, key: str) -> int: ...
    def delete(self, key: str) -> int: ...
    def conn(self) -> Any: ...

def require(payload: Mapping[str, Any], key: str, *, target: str) -> Any:
    v = payload.get(key)
    if v is None or v == "":
        raise ValidationAppError(f"payload '{key}' is required", target=target)
    return v


def try_acquire_lock(
    redis_client: RedisClientLike, key: str, ttl_sec: int
) -> str | None:
    token = uuid.uuid4().hex
    redis_conn = redis_client.conn()
    ok = redis_conn.set(key, token.encode("utf-8"), nx=True, ex=ttl_sec)
    return token if ok else None


def release_lock(redis_client: RedisClientLike, key: str, token: str) -> None:
    # 토큰 일치할 때만 해제(최소 안전장치)
    redis_conn = redis_client.conn()
    cur = redis_conn.get(key)
    if cur is None:
        return
    try:
        cur_s = cur.decode("utf-8", errors="ignore")
    except Exception:
        return
    if cur_s == token:
        redis_client.delete(key)


def skip(reason: str) -> dict:
    return {"ok": True, "skipped": True, "reason": reason}

