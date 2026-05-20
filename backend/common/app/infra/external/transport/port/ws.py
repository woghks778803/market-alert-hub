from dataclasses import dataclass
from typing import Any, AsyncIterator, Protocol


@dataclass(frozen=True)
class WsConnectConfig:
    url: str
    ping_interval_sec: float | None = 20.0
    close_timeout_sec: float = 5.0


class WsConnection(Protocol):
    async def send(self, data: str | bytes) -> None: ...
    async def recv(self) -> bytes | str: ...
    async def close(self) -> None: ...


class AsyncWsTransport(Protocol):
    async def connect(self, cfg: WsConnectConfig) -> WsConnection: ...
