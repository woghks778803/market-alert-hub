import asyncio
import json
import os
from typing import Any, Dict

import redis.asyncio as redis

from app.ws.hub.manager import Hub


async def run_redis_consumer(
    hub: Hub,
    *,
    redis_url: str | None = None,
    stream_key: str | None = None,
    block_ms: int = 1000,
) -> None:
    url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379/0")
    key = stream_key or os.getenv(
        "TICK_STREAM_KEY", "market-alert-hub:local:stream:tickers:BINANCE:BTCUSDT"
    )
    r = redis.from_url(url)
    last_id = "0-0"
    candles: Dict[str, Dict[str, Any]] = {}

    try:
        while True:
            resp = await r.xread(streams={key: last_id}, count=100, block=block_ms)
            if not resp:
                await asyncio.sleep(0)
                continue

            for _, entries in resp:
                for entry_id, fields in entries:
                    last_id = entry_id.decode() if isinstance(entry_id, bytes) else entry_id
                    payload = _decode_payload(fields)
                    if not payload:
                        continue
                    await _handle_tick(payload, candles, hub)
    except asyncio.CancelledError:
        raise
    finally:
        await r.close()


def _decode_payload(fields: dict) -> dict[str, Any] | None:
    raw = fields.get(b"payload") or fields.get("payload")
    if not raw:
        return None
    try:
        text = raw.decode() if isinstance(raw, (bytes, bytearray)) else raw
        data = json.loads(text)
        if isinstance(data, dict):
            return data
    except Exception:
        return None
    return None


async def _handle_tick(
    tick: dict[str, Any],
    candles: Dict[str, Dict[str, Any]],
    hub: Hub,
) -> None:
    symbol = tick.get("symbol")
    ts = tick.get("timestamp")
    price = tick.get("price")
    vol = tick.get("volume") or 0
    if not isinstance(symbol, str) or ts is None or price is None:
        return

    sec = int(ts) // 1000
    state = candles.get(symbol)

    if state and state["second"] == sec:
        state["high"] = max(state["high"], price)
        state["low"] = min(state["low"], price)
        state["close"] = price
        state["volume"] += vol
    else:
        if state:
            candle = _to_candle(symbol, state)
            await hub.broadcast(symbol, candle)
        candles[symbol] = {
            "second": sec,
            "open": price,
            "high": price,
            "low": price,
            "close": price,
            "volume": vol,
        }


def _to_candle(symbol: str, state: Dict[str, Any]) -> dict[str, Any]:
    return {
        "type": "candle_1s",
        "symbol": symbol,
        "open": state["open"],
        "high": state["high"],
        "low": state["low"],
        "close": state["close"],
        "volume": state["volume"],
        "timestamp": state["second"],
    }
