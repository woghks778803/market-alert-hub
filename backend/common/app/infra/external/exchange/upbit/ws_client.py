import asyncio
import json
import uuid
from dataclasses import dataclass
from typing import Any, AsyncIterator

import websockets
from websockets import WebSocketClientProtocol

from .errors import UpbitWsError, UpbitDecodeError
from .types import UpbitWsSubscribe, StreamItem


@dataclass(frozen=True)
class UpbitWsClientConfig:
    url: str = "wss://api.upbit.com/websocket/v1"
    ping_interval_sec: float | None = 20.0  # 라이브러리 ping 사용
    close_timeout_sec: float = 5.0


class UpbitWsClient:
    """
    - '연결 자체(transport)'는 websockets 라이브러리에게 맡김(transport 보류)
    - 이 클래스는 Upbit WS 구독/수신을 얇게 감싸는 어댑터 역할
    """

    def __init__(self, config: UpbitWsClientConfig | None = None) -> None:
        self._config = config or UpbitWsClientConfig()

    async def stream_once(
        self,
        *,
        subscribe: UpbitWsSubscribe,
        cursor: str | None,
        stop_event: asyncio.Event,
    ) -> AsyncIterator[StreamItem]:
        """
        collector가 기대하는 형태로 (cursor, payload)를 yield.
        - cursor는 여기서 '마지막 메시지 id' 같은 걸로 만들어도 되고,
          당장은 "uuid+seq" 같은 더미로 시작해도 됨.
        - stop_event가 set되면 빠져나가도록 설계.
        """
        # Upbit WS는 흔히 ticket + subscribe objects 형태로 보냄
        frames = [{"ticket": str(uuid.uuid4())}] + subscribe.to_frames()
        payload_bytes = json.dumps(frames).encode("utf-8")

        try:
            async with websockets.connect(
                self._config.url,
                ping_interval=self._config.ping_interval_sec,
                close_timeout=self._config.close_timeout_sec,
            ) as ws:
                await ws.send(payload_bytes)

                async for msg in self._iter_messages(ws, stop_event):
                    payload = self._decode_message(msg)
                    # cursor 생성: 지금은 최소 스켈레톤이므로 단순화
                    # 실제로는 payload의 seq/timestamp 등을 사용하도록 교체
                    new_cursor = self._derive_cursor(payload, fallback=cursor)
                    yield StreamItem(cursor=new_cursor, payload=payload)

        except asyncio.CancelledError:
            # 상위(run/finally cancel)에서 내려오는 취소는 그대로 전파
            raise
        except Exception as e:
            raise UpbitWsError(f"Upbit ws stream failed: {e}") from e

    async def _iter_messages(
        self,
        ws: WebSocketClientProtocol,
        stop_event: asyncio.Event,
    ) -> AsyncIterator[bytes | str]:
        """
        websockets는 기본적으로 텍스트(str) 또는 바이너리(bytes)를 반환.
        stop_event가 set되면 탈출.
        """
        while not stop_event.is_set():
            # recv()는 cancel이 잘 먹는 편이라, 종료 시 cancel로 빠질 가능성이 높음
            msg = await ws.recv()
            yield msg

    def _decode_message(self, msg: bytes | str) -> dict[str, Any]:
        """
        Upbit WS는 bytes로 오는 경우가 많아서 bytes/str 모두 처리.
        """
        try:
            if isinstance(msg, bytes):
                text = msg.decode("utf-8")
            else:
                text = msg
            data = json.loads(text)
            if not isinstance(data, dict):
                raise UpbitDecodeError("Unexpected ws payload shape")
            return data
        except UpbitDecodeError:
            raise
        except Exception as e:
            raise UpbitDecodeError(f"Failed to decode Upbit ws message: {e}") from e

    def _derive_cursor(self, payload: dict[str, Any], *, fallback: str | None) -> str:
        """
        cursor 정책은 나중에 확정(예: seq, timestamp, trade_id 등).
        일단은 payload에 쓸만한 값이 있으면 쓰고, 없으면 UUID로 대체.
        """
        for key in ("seq", "timestamp", "trade_id", "tms"):
            v = payload.get(key)
            if v is not None:
                return str(v)
        return fallback or str(uuid.uuid4())


def get_ws_client(config: UpbitWsClientConfig) -> UpbitWsClient:
    return UpbitWsClient(config)