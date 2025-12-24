import json
import logging
import os
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol

logger = logging.getLogger(__name__)


class CheckpointStore(Protocol):
    """
    '어디까지 처리했는지'를 저장/조회하는 저장소 인터페이스.

    - key: 논리적 이름(예: "catalog_sync", "upbit_ws:ticker", "candles_1m:KRW-BTC")
    - value: JSON 직렬화 가능한 dict
    """

    async def get(self, key: str) -> dict[str, Any] | None: ...

    async def set(self, key: str, value: dict[str, Any]) -> None: ...

    async def delete(self, key: str) -> None: ...


# ---------------------------
# Memory
# ---------------------------


@dataclass
class MemoryCheckpointStore:
    """
    프로세스 메모리에만 저장. (재시작하면 사라짐)
    개발/로컬 테스트에 유용.
    """

    _data: dict[str, dict[str, Any]] = field(default_factory=dict)

    async def get(self, key: str) -> dict[str, Any] | None:
        return self._data.get(key)

    async def set(self, key: str, value: dict[str, Any]) -> None:
        self._data[key] = value

    async def delete(self, key: str) -> None:
        self._data.pop(key, None)


# ---------------------------
# File
# ---------------------------


@dataclass
class FileCheckpointStore:
    """
    단일 JSON 파일에 key->value map을 저장.

    - 장점: 외부 의존성 없음, 재시작 후에도 유지
    - 단점: 여러 인스턴스가 동시에 쓰면 충돌 가능(단일 인스턴스 전제에 적합)
    """

    path: str

    def _read_all(self) -> dict[str, dict[str, Any]]:
        p = Path(self.path)
        if not p.exists():
            return {}
        try:
            raw = p.read_text(encoding="utf-8")
            if not raw.strip():
                return {}
            data = json.loads(raw)
            if not isinstance(data, dict):
                return {}
            # 타입 안정성은 최소 수준으로만
            return {str(k): v for k, v in data.items() if isinstance(v, dict)}
        except Exception:
            logger.exception("checkpoint file read failed path=%s", self.path)
            return {}

    def _atomic_write(self, data: dict[str, dict[str, Any]]) -> None:
        p = Path(self.path)
        p.parent.mkdir(parents=True, exist_ok=True)

        # atomic replace: temp file -> replace
        fd, tmp_path = tempfile.mkstemp(prefix=p.name + ".", dir=str(p.parent))
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp_path, self.path)
        finally:
            try:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)
            except Exception:
                # best-effort cleanup
                pass

    async def get(self, key: str) -> dict[str, Any] | None:
        return self._read_all().get(key)

    async def set(self, key: str, value: dict[str, Any]) -> None:
        data = self._read_all()
        data[key] = value
        self._atomic_write(data)

    async def delete(self, key: str) -> None:
        data = self._read_all()
        if key in data:
            data.pop(key, None)
            self._atomic_write(data)


# ---------------------------
# Redis (optional)
# ---------------------------


@dataclass
class RedisCheckpointStore:
    """
    Redis에 key별로 JSON을 저장.

    - 장점: 재시작/다중 인스턴스에도 안전(실무에 가장 추천)
    - 단점: redis 의존성 필요

    구현 디테일:
    - Redis에는 'string value'로 JSON을 저장한다.
    - prefix로 네임스페이스를 분리한다.
    """

    redis_url: str
    key_prefix: str = "collector:checkpoint:"
    _client: Any | None = None  # lazy init

    def _full_key(self, key: str) -> str:
        return f"{self.key_prefix}{key}"

    async def _get_client(self):
        if self._client is not None:
            return self._client

        try:
            # redis-py 4.x: redis.asyncio 제공
            import redis.asyncio as redis  # type: ignore
        except Exception as e:
            raise RuntimeError(
                "RedisCheckpointStore requires 'redis' package with asyncio support. "
                "Install redis-py (pip install redis)."
            ) from e

        self._client = redis.from_url(self.redis_url, decode_responses=True)
        return self._client

    async def get(self, key: str) -> dict[str, Any] | None:
        client = await self._get_client()
        raw = await client.get(self._full_key(key))
        if raw is None:
            return None
        try:
            data = json.loads(raw)
            return data if isinstance(data, dict) else None
        except Exception:
            logger.exception("redis checkpoint decode failed key=%s", key)
            return None

    async def set(self, key: str, value: dict[str, Any]) -> None:
        client = await self._get_client()
        raw = json.dumps(value, ensure_ascii=False, separators=(",", ":"))
        await client.set(self._full_key(key), raw)

    async def delete(self, key: str) -> None:
        client = await self._get_client()
        await client.delete(self._full_key(key))

    async def close(self) -> None:
        """
        (선택) 프로세스 종료 시 close 호출하면 커넥션 정리 가능.
        run.py 쪽에서 stop_event 시점에 호출해도 됨.
        """
        if self._client is None:
            return
        try:
            await self._client.close()
        finally:
            self._client = None
