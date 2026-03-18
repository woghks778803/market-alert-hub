import uuid
import json
from typing import Any, Mapping, Protocol, runtime_checkable

from app.exception_handlers import ValidationHandler

_META_FIELDS = {"started_at", "count"}


@runtime_checkable
class RedisClientLike(Protocol):
    """
    worker jobs 레벨에서 필요한 최소 API.
    """

    def ttl(self, key: str) -> int: ...
    def delete(self, key: str) -> int: ...
    def conn(self) -> Any: ...


def require(payload: Mapping[str, Any], key: str, *, target: str) -> Any:
    v = payload.get(key)
    if v is None or v == "":
        raise ValidationHandler(f"payload '{key}' is required", target=target)
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

    lua = """
        if redis.call("get", KEYS[1]) == ARGV[1] then
            return redis.call("del", KEYS[1])
        else
            return 0
        end
    """

    try:
        # redis-py는 보통 str/bytes 모두 허용. 값은 bytes로 저장했으니 token도 bytes로 비교
        redis_conn.eval(lua, 1, key, token.encode("utf-8"))
    except Exception:
        return

    # cur = redis_conn.get(key)
    # if cur is None:
    #     return
    # try:
    #     cur_s = cur.decode("utf-8", errors="ignore")
    # except Exception:
    #     return
    # if cur_s == token:
    #     redis_client.delete(key)


def _bytes_to_str(x) -> str:
    if x is None:
        return ""
    if isinstance(x, bytes):
        return x.decode("utf-8", errors="ignore")
    return str(x)


def _str_to_int(x: Any, default: int = 0) -> int:
    try:
        return int(_bytes_to_str(x))
    except Exception:
        return default


def load_snap_json_map(redis_client: RedisClientLike, key: str) -> dict[str, dict]:
    """
    HGETALL 결과를 {field(str): payload(dict)}로 변환.
    started_at/count 같은 메타 field는 제외.
    """
    raw = redis_client.conn().hgetall(key) or {}
    out: dict[str, dict] = {}
    for k, v in raw.items():
        ks = _bytes_to_str(k)
        if not ks or ks in _META_FIELDS:
            continue
        try:
            out[ks] = json.loads(_bytes_to_str(v)) if v else {}
        except Exception:
            out[ks] = {}
    return out


def load_ticker_ticks(
    redis_client: RedisClientLike,
    *,
    key: str,
    bucket_start_epoch: int,
    bucket_end_epoch: int,
    max_count: int = 600,
) -> list[dict[str, Any]]:
    """
    Redis Stream(1초틱)에서 버킷 범위 [start, end) 데이터를 읽어온다.

    stream key: {app}:{env}:stream:ticker:{EXCHANGE}:{SYMBOL}
    stream item fields(예시):
      - b"ts": b"1769..." (ms)
      - b"p" : b'{"type":"candle.1s", ...}'  (json payload)

    반환: payload(dict) 리스트 (필요하면 ts_ms를 같이 주입)
    """
    r = redis_client.conn()

    start_ms = int(bucket_start_epoch) * 1000
    end_ms = int(bucket_end_epoch) * 1000

    # stream id는 "{ms}-{seq}" 형태라 시간 범위를 id로 바로 자를 수 있음.
    min_id = f"{start_ms}-0"
    max_id = f"{end_ms}-0"  # XRANGE max는 inclusive라 end boundary는 아래에서 ts로 한번 더 걸러줌.

    rows = r.xrange(key, min=min_id, max=max_id, count=max_count)

    out: list[dict[str, Any]] = []
    for _id, fields in rows:
        # fields key/value가 bytes일 수 있음
        ts_ms = _str_to_int(fields.get(b"ts") or fields.get("ts"), default=0)
        if ts_ms and not (start_ms <= ts_ms < end_ms):
            continue

        raw_p = fields.get(b"p") or fields.get("p")
        if not raw_p:
            continue

        try:
            payload = json.loads(_bytes_to_str(raw_p))
        except Exception:
            continue

        # 디버깅/후속 처리에 유용하면 ts_ms를 payload에 주입
        if ts_ms:
            payload.setdefault("_ts_ms", ts_ms)
        payload.setdefault("_stream_id", _bytes_to_str(_id))

        out.append(payload)

    return out
