import asyncio
import json
import uuid
from decimal import Decimal
from dataclasses import dataclass
from typing import Any, AsyncIterator, AsyncIterable

from .shared.errors import UpbitWsError, UpbitDecodeError
from .shared.types import (
    UpbitWsSubscribe,
)

from app.infra.external.exchange.port.ws_client import (
    WsStreamItem,
    WsClient,
    WsStream,
)
from app.infra.external.transport.port.ws import (
    AsyncWsTransport,
    WsConnectConfig,
)
from app.infra.external.transport.impl.websockets import WebsocketsTransport


@dataclass(frozen=True)
class UpbitWsClientConfig:
    url: str = "wss://api.upbit.com/websocket/v1"
    ping_interval_sec: float | None = 20.0
    close_timeout_sec: float = 5.0


class UpbitWsClient(WsClient):
    """
    - transport(연결/송수신)은 AsyncWsTransport에게 위임
    - 여기서는 Upbit 구독 프레임 생성 + 메시지 decode만 담당
    """

    def __init__(
        self,
        config: UpbitWsClientConfig | None = None,
        *,
        transport: AsyncWsTransport | None = None,
    ) -> None:
        self._config = config or UpbitWsClientConfig()
        self._transport = transport or WebsocketsTransport()

    async def stream_once(
        self,
        *,
        subscribe: UpbitWsSubscribe,
        cursor: str | None,
        stop_event: asyncio.Event,
    ) -> WsStream:
        frames = [{"ticket": str(uuid.uuid4())}] + subscribe.to_frames()
        payload_bytes = json.dumps(frames).encode("utf-8")

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
                new_cursor = self._derive_cursor(payload, fallback=cursor)

                normalized = self._normalize_ticker(payload)
                # print("upbit normalized", normalized)
                yield (new_cursor, normalized)

        except asyncio.CancelledError:
            raise
        except Exception as e:
            raise UpbitWsError(f"Upbit ws stream failed: {e}") from e
        finally:
            try:
                await conn.close()
            except Exception:
                # close 실패는 스트림 실패보다 중요하지 않음
                pass

    async def _iter_messages(
        self,
        conn,
        stop_event: asyncio.Event,
    ) -> AsyncIterator[bytes | str]:
        """
        stop_event를 즉시 반영하려고 recv를 무한 대기시키지 않는다.
        - recv task vs stop_event task 레이스
        """
        while not stop_event.is_set():
            recv_task = asyncio.create_task(conn.recv())
            stop_task = asyncio.create_task(stop_event.wait())

            done, pending = await asyncio.wait(
                {recv_task, stop_task},
                return_when=asyncio.FIRST_COMPLETED,
            )

            for t in pending:
                t.cancel()

            # 첫 task cancel 중 다른 task await 방지
            for t in pending:
                try:
                    await t
                except asyncio.CancelledError:
                    pass

            if stop_task in done:
                # 종료 신호 우선
                return

            # recv 완료
            yield recv_task.result()

    def _decode_message(self, msg: bytes | str) -> dict[str, Any]:
        try:
            text = msg.decode("utf-8") if isinstance(msg, bytes) else msg
            data = json.loads(text)
            if not isinstance(data, dict):
                raise UpbitDecodeError("Unexpected ws payload shape")
            return data
        except UpbitDecodeError:
            raise
        except Exception as e:
            raise UpbitDecodeError(f"Failed to decode Upbit ws message: {e}") from e

    def _normalize_ticker(self, payload: dict[str, Any]) -> dict[str, Any]:
        if payload.get("type") != "candle.1s":
            return {
                "status": "skip",
                "reason": "skip_event",
            }

        try:
            symbol = payload["code"]  # KRW-BTC
            # NOTE: Decimal 연산 처리 지연
            # price = Decimal(str(payload["trade_price"]))  # 현재가
            # volume = Decimal(str(payload["candle_acc_trade_volume"]))  # 누적 거래량
            price = float(payload["trade_price"])
            volume = float(payload["candle_acc_trade_volume"])
            timestamp = int(payload["timestamp"])  # ms timestamp
        except (KeyError, ValueError, TypeError):
            return {
                "status": "fail",
                "reason": "parse_error",
                "raw": payload,
            }

        return {
            "status": "success",
            "data": {
                "symbol": symbol,
                "price": price,
                "volume": volume,
                "timestamp": timestamp,
            },
        }

    def _derive_cursor(self, payload: dict[str, Any], *, fallback: str | None) -> str:
        for key in ("seq", "timestamp", "trade_id", "tms"):
            v = payload.get(key)
            if v is not None:
                return str(v)
        return fallback or str(uuid.uuid4())


def get_upbit_ws_client(config: UpbitWsClientConfig) -> UpbitWsClient:
    return UpbitWsClient(config)
