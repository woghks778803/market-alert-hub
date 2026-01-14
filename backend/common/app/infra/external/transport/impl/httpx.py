import httpx
from dataclasses import dataclass
from typing import Any
from app.infra.external.transport.port.http import HttpResponse, SyncHttpTransport


@dataclass(frozen=True)
class HttpxTransportConfig:
    base_url: str
    timeout_sec: float = 10.0


class HttpxSyncTransport(SyncHttpTransport):
    def __init__(self, config: HttpxTransportConfig) -> None:
        self._config = config
        self._client: httpx.Client | None = None

    def __enter__(self) -> "HttpxSyncTransport":
        self._ensure()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def _ensure(self) -> None:
        if self._client is not None:
            return
        self._client = httpx.Client(
            base_url=self._config.base_url,
            timeout=httpx.Timeout(self._config.timeout_sec),
        )

    def get(self, path: str, *, params: dict[str, Any] | None = None) -> HttpResponse:
        self._ensure()
        assert self._client is not None
        r = self._client.get(path, params=params)
        return HttpResponse(status_code=r.status_code, text=r.text)

    def close(self) -> None:
        if self._client is None:
            return
        self._client.close()
        self._client = None
