import asyncio
import json
import uuid
from dataclasses import dataclass
from typing import Any, AsyncIterator

from .shared.errors import BinanceWsError, BinanceDecodeError
from .shared.types import BinanceWsSubscribe

from app.infra.external.exchange.port.ws_client import (
    WsClient,
    WsStream,
    WsCursor,
)
from app.infra.external.transport.port.ws import (
    AsyncWsTransport,
    WsConnectConfig,
)
from app.infra.external.transport.impl.websockets import WebsocketsTransport


@dataclass(frozen=True)
class BinanceWsClientConfig:
    url: str = "wss://stream.binance.com:9443/ws"
    ping_interval_sec: float | None = 20.0
    close_timeout_sec: float = 5.0


class BinanceWsClient(WsClient):
    """
    - transport(연결/송수신)은 AsyncWsTransport에게 위임
    - 여기서는 Binance 구독 프레임 생성 + 메시지 decode/정규화만 담당
    """

    def __init__(
        self,
        config: BinanceWsClientConfig | None = None,
        *,
        transport: AsyncWsTransport | None = None,
    ) -> None:
        self._config = config or BinanceWsClientConfig()
        self._transport = transport or WebsocketsTransport()

    async def stream_once(
        self,
        *,
        subscribe: BinanceWsSubscribe,
        cursor: WsCursor,
        stop_event: asyncio.Event,
    ) -> WsStream:
        payload_bytes = json.dumps(subscribe.to_payload()).encode("utf-8")

        conn = await self._transport.connect(
            WsConnectConfig(
                url=self._config.url,
                ping_interval_sec=self._config.ping_interval_sec,
                close_timeout_sec=self._config.close_timeout_sec,
            )
        )

        try:
            await conn.send(payload_bytes)
            async for msg in self._iter_messages(conn, stop_event):
                payload = self._decode_message(msg)

                # 구독 ACK ("result": null) 는 스킵
                if "result" in payload:
                    continue

                normalized = self._normalize_ticker(payload)
                if normalized is None:
                    continue

                new_cursor = self._derive_cursor(payload, fallback=cursor)
                yield (new_cursor, normalized)

        except asyncio.CancelledError:
            raise
        except Exception as e:
            raise BinanceWsError(f"Binance ws stream failed: {e}") from e
        finally:
            try:
                await conn.close()
            except Exception:
                pass

    async def _iter_messages(
        self,
        conn: Any,
        stop_event: asyncio.Event,
    ) -> AsyncIterator[bytes | str]:
        while not stop_event.is_set():
            while True:
                if stop_event.is_set():
                    return

                try:
                    msg = await asyncio.wait_for(conn.recv(), timeout=1)
                    yield msg
                except asyncio.TimeoutError:
                    continue

    def _decode_message(self, msg: bytes | str) -> dict[str, Any]:
        try:
            text = msg.decode("utf-8") if isinstance(msg, bytes) else msg
            data = json.loads(text)
            if not isinstance(data, dict):
                raise BinanceDecodeError("Unexpected ws payload shape")
            return data
        except BinanceDecodeError:
            raise
        except Exception as e:
            raise BinanceDecodeError(f"Failed to decode Binance ws message: {e}") from e

    def _normalize_ticker(self, payload: dict[str, Any]) -> dict[str, Any] | None:
        # 필요한 필드가 없으면 스킵
        if not {"s", "c", "v", "E"} <= payload.keys():
            return None

        return {
            "symbol": payload.get("s"),
            "price": payload.get("c"),
            "volume": payload.get("v"),
            "timestamp": payload.get("E"),
        }

    def _derive_cursor(self, payload: dict[str, Any], *, fallback: WsCursor) -> str:
        ts = payload.get("E")
        sym = payload.get("s")
        if ts is not None and sym is not None:
            return f"{sym}:{ts}"
        if ts is not None:
            return str(ts)
        return fallback or str(uuid.uuid4())


def get_binance_ws_client(config: BinanceWsClientConfig) -> BinanceWsClient:
    return BinanceWsClient(config)
