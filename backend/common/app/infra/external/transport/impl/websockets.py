import websockets
from websockets import WebSocketClientProtocol
from app.infra.external.transport.port.ws import (
    AsyncWsTransport,
    WsConnectConfig,
    WsConnection,
)


class _WebsocketsConnection(WsConnection):
    def __init__(self, ws: WebSocketClientProtocol) -> None:
        self._ws = ws

    async def send(self, data: bytes) -> None:
        await self._ws.send(data)

    async def recv(self) -> bytes | str:
        return await self._ws.recv()

    async def close(self) -> None:
        await self._ws.close()


class WebsocketsTransport(AsyncWsTransport):
    async def connect(self, cfg: WsConnectConfig) -> WsConnection:
        ws = await websockets.connect(
            cfg.url,
            ping_interval=cfg.ping_interval_sec,
            close_timeout=cfg.close_timeout_sec,
        )
        return _WebsocketsConnection(ws)
