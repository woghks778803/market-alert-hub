# import asyncio
from typing import Any, AsyncIterator, Callable, Protocol, TypeAlias
from collections.abc import AsyncIterable, Callable

WsPayload: TypeAlias = dict[str, Any]
WsCursor: TypeAlias = str | None
# (new_cursor, payload)
WsStreamItem: TypeAlias = tuple[WsCursor, WsPayload]
WsStream = AsyncIterable[WsStreamItem]
StreamFactory = Callable[[str | None, Any], WsStream]
StreamFactoryRegistry = dict[str, StreamFactory]


class WsClient(Protocol):
    """
    거래소별 WS 클라이언트(어댑터) 포트.
    - transport(websockets/httpx) 모름
    - collector 루프가 소비 가능한 형태로 yield만 보장
    """

    def stream_once(
        self,
        *,
        subscribe: Any,
        cursor: WsCursor,
        stop_event: Any,
    ) -> WsStream: ...

    """
    NOTE (typing):
    - 이 메서드는 "코루틴"이 아니라 "async generator"로 쓰는 게 의도다.
        (연결 1회 열고, 메시지마다 yield하는 형태)

    - 따라서 호출부는 보통 이렇게 쓴다:
        async for item in ws.stream_once(...):
            ...

    - 다만 Protocol(typing.Protocol) 안에서 `async def ... -> AsyncIterator[...]` 형태로 선언하면,
        Pylance가 이를 `Coroutine[..., AsyncIterator[...]]`로 오해하는 경우가 있다.
        런타임 동작은 정상이어도 정적 타입 경고가 날 수 있음.

    - 타입 경고를 피하고 싶다면:
        * Protocol 쪽 시그니처는 `def stream_once(...) -> AsyncIterator[...]`로 두고
        * 구현체는 실제로 `async def` + `yield`를 사용해 async generator를 구현한다.
    """


WsFactory: TypeAlias = Callable[[], WsClient]
WsFactoryRegistry: TypeAlias = dict[str, WsFactory]
