import asyncio
import json
import time
from typing import Any, Callable, Mapping
from app.core.constants import SNAP, STREAM

JsonDict = dict[str, Any]


def _pick_symbol(payload: Any) -> str | None:
    if not isinstance(payload, dict):
        return None
    for k in ("code", "symbol", "market", "exchange_symbol"):
        v = payload.get(k)
        if isinstance(v, str) and v:
            return v
    return None


def _pick_ts_ms(payload: Any) -> str:
    # 업비트 ticker는 timestamp(ms) 필드가 보통 있음. 없으면 현재시각(ms)
    if isinstance(payload, dict):
        for k in ("timestamp", "trade_timestamp", "ts", "time"):
            v = payload.get(k)
            if isinstance(v, (int, float)):
                # 초 단위로 들어오는 경우가 있으면 ms로 보정하고 싶으면 여기서 처리
                return str(int(v))
    return str(int(time.time() * 1000))


async def _sleep_or_stop(stop_event: asyncio.Event, seconds: float) -> None:
    if seconds <= 0:
        return
    try:
        await asyncio.wait_for(stop_event.wait(), timeout=seconds)
    except asyncio.TimeoutError:
        return


async def _maybe_await(v: Any) -> Any:
    if asyncio.iscoroutine(v):
        return await v
    return v


async def _ckpt_get(store: Any, key: str) -> str | None:
    get = getattr(store, "get", None)
    if get is None:
        return None
    v = get(key)
    v = await _maybe_await(v)
    return v


async def _ckpt_set(store: Any, key: str, value: str) -> None:
    set_ = getattr(store, "set", None)
    if set_ is None:
        return
    v = set_(key, value)
    await _maybe_await(v)


async def _fetch_codes(active_catalog: Any, exchange_code: str) -> list[str]:
    """
    active_catalog.get_symbols_snap(exchange_code) -> Mapping[str, JsonDict]
    (field=exchange_symbol, value=payload)
    """
    snap = await _maybe_await(active_catalog.get_symbols_snap(exchange_code))
    if not snap:
        return []
    keys = list(getattr(snap, "keys", lambda: [])())
    codes = [c for c in keys if isinstance(c, str) and c]
    # 중복 제거 + 정렬(로그/비교 안정성)
    return sorted(set(codes))


async def upsert_marketdata_and_buffer_5m(
    payload: Any,
    exchange_code: str,
    *,
    redis: Any,  # redis.asyncio.Redis (duck-typing)
    snap_key_fn: Callable[[str], str],  # ex) lambda ex: f"{app}:{env}:snap:ticker:{ex}"
    stream_key_fn: Callable[
        [str, str], str
    ],  # ex) lambda ex,sym: f"{app}:{env}:stream:ticker:{ex}:{sym}"
    maxlen: int = 600,  # 심볼당 최근 N개(= 5분 근사)
    ttl_sec: int = 600,  # stream 키 TTL (여유 있게 10분 추천)
) -> None:
    symbol = _pick_symbol(payload)
    if not symbol or not isinstance(payload, dict):
        return

    snap_key = snap_key_fn(exchange_code)
    stream_key = stream_key_fn(exchange_code, symbol)

    # 저장 포맷: payload 전체 json(가볍게) + ts(ms)
    payload_json = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    ts_ms = _pick_ts_ms(payload)

    # 파이프라인으로 한번에 처리
    pipe = redis.pipeline(transaction=True)
    pipe.hset(snap_key, symbol, payload_json)

    # Stream 엔트리는 너무 큰 필드명/구조 피하고 최소화
    pipe.xadd(stream_key, {"ts": ts_ms, "p": payload_json})

    # print(f"[stream_marketdata] upsert snap {snap_key} [{symbol}]")
    # print(f"[stream_marketdata] upsert stream {stream_key} [{symbol}]")
    # print(payload_json)

    # 최근 N개 유지(근사) - redis-py 시그니처 차이 대비
    try:
        pipe.xtrim(stream_key, maxlen=maxlen, approximate=True)
    except TypeError:
        # 구버전/다른 시그니처 대응
        pipe.xtrim(stream_key, maxlen)

    pipe.expire(stream_key, ttl_sec)

    await pipe.execute()


async def run_stream_marketdata_loop(
    *,
    stop_event: asyncio.Event,
    checkpoint_store: Any,
    ctx: Any,
    exchange_code: str,
    reconnect_backoff_sec: float,
    checkpoint_key: str,
    symbols_poll_sec: float = 2.0,
    min_resubscribe_interval_sec: float = 1.0,
) -> None:
    """
    - exchange_code 단위로 1개 loop 실행 (심볼당 X)
    - 심볼 목록은 Redis snapshot에서 주기적으로 읽어서 변경되면 재구독
    - loop 내부 create_task() 없이, 소비 중간중간 폴링하여 재구독 트리거
    """

    cfg = ctx.config
    snap_key_fn = lambda ex: f"{cfg.app_name}:{cfg.deploy_env}:{SNAP}:ticker:{ex}"
    stream_key_fn = (
        lambda ex, sym: f"{cfg.app_name}:{cfg.deploy_env}:{STREAM}:ticker:{ex}:{sym}"
    )
    active_catalog = ctx.active_catalog
    redis = ctx.async_redis_client.conn()
    ws_factory = ctx.ws_facs_register[exchange_code]
    subscribe_factory = ctx.subscribe_facs_register[exchange_code]

    cursor: str | None = await _ckpt_get(checkpoint_store, checkpoint_key)

    last_codes: list[str] = []
    last_resubscribe_at = 0.0

    attempt = 0
    while not stop_event.is_set():
        try:
            # 1) 현재 codes 확보
            codes = await _fetch_codes(active_catalog, exchange_code)
            # print(f"[stream_marketdata] fetched codes for {exchange_code}: {codes}")

            # codes가 비면 차트 수집은 대기
            if not codes:
                last_codes = []
                await _sleep_or_stop(stop_event, min(symbols_poll_sec, 5.0))
                continue

            # (재구독 최소 간격) 너무 잦은 reconnect 방지
            now = time.monotonic()
            if (
                last_codes
                and codes != last_codes
                and (now - last_resubscribe_at) < min_resubscribe_interval_sec
            ):
                await _sleep_or_stop(
                    stop_event,
                    min_resubscribe_interval_sec - (now - last_resubscribe_at),
                )
                continue

            last_codes = codes
            last_resubscribe_at = time.monotonic()

            # 2) subscribe 만들고 스트림 소비
            subscribe = subscribe_factory(codes)
            ws = ws_factory()

            next_poll_at = time.monotonic() + symbols_poll_sec
            session_stop = False

            async for new_cursor, payload in ws.stream_once(
                subscribe=subscribe,
                cursor=cursor,
                stop_event=stop_event,  # stop_event만 전달 (재구독은 break로 처리)
            ):
                if stop_event.is_set():
                    break

                await upsert_marketdata_and_buffer_5m(
                    payload,
                    exchange_code,
                    redis=redis,
                    snap_key_fn=snap_key_fn,
                    stream_key_fn=stream_key_fn,
                )

                # cursor 저장
                if new_cursor is not None and new_cursor != cursor:
                    cursor = new_cursor
                    await _ckpt_set(checkpoint_store, checkpoint_key, new_cursor)

                # 3) 메시지 소비 중 주기적으로 codes 변경 감지 → 바뀌면 break 후 재구독
                now = time.monotonic()
                if now >= next_poll_at:
                    next_poll_at = now + symbols_poll_sec
                    new_codes = await _fetch_codes(active_catalog, exchange_code)
                    if new_codes != last_codes:
                        last_codes = new_codes
                        session_stop = True
                        break

            if session_stop:
                # 바로 다음 루프에서 재구독 진행
                continue

            # 정상 종료(대개 stop_event set) 아닌데 async for가 끝났으면 짧게 쉬고 재연결
            if not stop_event.is_set():
                await _sleep_or_stop(stop_event, 0.2)

            attempt = 0

        except asyncio.CancelledError:
            raise
        except Exception:
            attempt += 1
            # 간단 백오프 (cap = reconnect_backoff_sec)
            cap = max(0.5, float(reconnect_backoff_sec))
            delay = min(cap, 0.5 * (2 ** min(attempt, 8)))
            await _sleep_or_stop(stop_event, delay)
