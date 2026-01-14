import asyncio
from typing import Any, AsyncIterator, Callable, Protocol, TypeAlias


WsPayload: TypeAlias = dict[str, Any]
WsCursor: TypeAlias = str | None

# (new_cursor, payload)
WsStreamItem: TypeAlias = tuple[WsCursor, WsPayload]


class WsClientPort(Protocol):
    """
    거래소별 WS 클라이언트(어댑터) 포트.
    - transport(websockets/httpx) 모름
    - collector 루프가 소비 가능한 형태로 yield만 보장
    """

    async def stream_once(
        self,
        *,
        subscribe: Any,
        cursor: WsCursor,
        stop_event: asyncio.Event,
    ) -> AsyncIterator[WsStreamItem]: ...


WsClientFactory: TypeAlias = Callable[[], WsClientPort]
WsClientRegistry: TypeAlias = dict[str, WsClientFactory]
