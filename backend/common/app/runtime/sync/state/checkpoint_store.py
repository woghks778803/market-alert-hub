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

    def get(self, key: str) -> dict[str, Any] | None: ...

    def set(self, key: str, value: dict[str, Any]) -> None: ...

    def delete(self, key: str) -> None: ...


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

    def get(self, key: str) -> dict[str, Any] | None:
        return self._data.get(key)

    def set(self, key: str, value: dict[str, Any]) -> None:
        self._data[key] = value

    def delete(self, key: str) -> None:
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

    def get(self, key: str) -> dict[str, Any] | None:
        return self._read_all().get(key)

    def set(self, key: str, value: dict[str, Any]) -> None:
        data = self._read_all()
        data[key] = value
        self._atomic_write(data)

    def delete(self, key: str) -> None:
        data = self._read_all()
        if key in data:
            data.pop(key, None)
            self._atomic_write(data)
