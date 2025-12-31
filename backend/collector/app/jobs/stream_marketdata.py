import asyncio
import logging
import random
from collections.abc import AsyncIterator, Callable
from typing import Any

logger = logging.getLogger(__name__)

# stream_once(cursor, stop_event) 가 yield 하는 형태:
#   (new_cursor, payload)
# - new_cursor: 체크포인트로 저장할 커서(시퀀스/타임스탬프/마지막 trade id 등)
# - payload: DB upsert 등 실제 처리 대상(아직 미정이니 Any)
StreamOnce = Callable[
    [str | None, asyncio.Event], AsyncIterator[tuple[str | None, Any]]
]


async def run_stream_marketdata_loop(
    *,
    stop_event: asyncio.Event,
    checkpoint_store: Any,
    reconnect_backoff_sec: float,
    stream_once: StreamOnce | None = None,
    checkpoint_key: str = "collector:market_stream:cursor",
) -> None:
    """
    Marketdata stream main loop.

    - stop_event 가 set 되면 즉시 종료
    - checkpoint_store 에서 cursor 로드/저장 (duck-typing: get/set or load/save 지원)
    - stream_once 를 1회 실행하고, 끊기면 백오프 후 재연결

    NOTE:
      실제 거래소 WebSocket/DB upsert는 stream_once 내부에서 처리하도록 분리해둔다.
      (현재는 wiring 단계가 미완이라 stream_once 는 나중에 주입)
    """
    if stream_once is None:
        stream_once = _not_wired_stream_once  # type: ignore[assignment]

    cursor: str | None = await _checkpoint_get(checkpoint_store, checkpoint_key)

    attempt = 0
    logger.info(
        "market_stream: start (checkpoint_key=%s, cursor=%s)", checkpoint_key, cursor
    )

    while not stop_event.is_set():
        try:
            # 스트림 1회 실행: 내부에서 연결 -> 수신 -> 처리 -> (필요시) new_cursor yield
            async for new_cursor, payload in stream_once(cursor, stop_event):
                # payload 처리는 stream_once가 책임지는 구조를 권장하지만,
                # 여기서도 훅을 넣고 싶으면 아래 주석을 활용.
                # await handle_payload(payload)

                if stop_event.is_set():
                    break

                if new_cursor is not None and new_cursor != cursor:
                    cursor = new_cursor
                    await _checkpoint_set(checkpoint_store, checkpoint_key, cursor)

            # 정상적으로 루프가 끝난 경우(예: stop_event set, 또는 stream_once가 종료)
            attempt = 0

            if not stop_event.is_set():
                # stream_once가 "정상 종료"했는데 stop이 아니라면, 너무 빠른 루프를 막기 위해 잠깐 쉼
                await _sleep_or_stop(stop_event, 0.2)

        except asyncio.CancelledError:
            raise
        except Exception:
            attempt += 1
            backoff = _calc_backoff(attempt, reconnect_backoff_sec)
            logger.exception(
                "market_stream: crashed; retry in %.2fs (attempt=%s)", backoff, attempt
            )
            await _sleep_or_stop(stop_event, backoff)

    logger.info("market_stream: stop (cursor=%s)", cursor)


def _calc_backoff(attempt: int, cap_sec: float) -> float:
    # 1,2,4,8... 지수 백오프 + 약간의 jitter, cap_sec 로 상한
    base = min(2 ** (attempt - 1), max(cap_sec, 0.5))
    jitter = random.uniform(0.0, base * 0.15)
    return min(base + jitter, max(cap_sec, 0.5))


async def _sleep_or_stop(stop_event: asyncio.Event, seconds: float) -> None:
    if seconds <= 0:
        return
    try:
        await asyncio.wait_for(stop_event.wait(), timeout=seconds)
    except asyncio.TimeoutError:
        return


async def _checkpoint_get(store: Any, key: str) -> str | None:
    """
    Duck-typing 지원:
      - await store.get(key) / store.get(key)
      - await store.load(key) / store.load(key)
    """
    for name in ("get", "load"):
        fn = getattr(store, name, None)
        if fn is None:
            continue
        val = fn(key)
        if asyncio.iscoroutine(val):
            val = await val
        if val is None:
            return None
        return str(val)
    return None


async def _checkpoint_set(store: Any, key: str, value: str) -> None:
    """
    Duck-typing 지원:
      - await store.set(key, value) / store.set(key, value)
      - await store.save(key, value) / store.save(key, value)
    """
    for name in ("set", "save"):
        fn = getattr(store, name, None)
        if fn is None:
            continue
        ret = fn(key, value)
        if asyncio.iscoroutine(ret):
            await ret
        return
    # store가 set/save를 지원하지 않으면 그냥 무시(런타임에서 바로 드러나게 로그)
    logger.warning("checkpoint_store has no set/save; key=%s value=%s", key, value)


async def _not_wired_stream_once(
    cursor: str | None, stop_event: asyncio.Event
) -> AsyncIterator[tuple[str | None, Any]]:
    # wiring 단계에서 실제 거래소 WebSocket stream_once 로 교체할 것
    raise RuntimeError("market_stream.stream_once is not wired yet")
    yield (cursor, None)  # pragma: no cover
