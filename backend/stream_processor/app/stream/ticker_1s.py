import time, json
from decimal import Decimal
from app.core.constants import STREAM, TICKERS
from app.core.util.datetime import utcnow, datetime_to_epoch_sec


async def run_ticker_1s_loop(
    *,
    stop_event,
    ctx,
    market_refresh_sec: float = 10.0,
):
    cfg = ctx.config
    catalog = ctx.facade.active_catalog
    candle = ctx.facade.candle_store
    redis = ctx.async_redis_client
    last_id = "$"  # 최신부터 시작
    key_prefix = f"{cfg.app_name}:{cfg.deploy_env}"

    buckets = {}  # symbol → state
    symbols_cache = {}
    last_refresh = 0

    while not stop_event.is_set():
        now = datetime_to_epoch_sec(utcnow())
        if (now - last_refresh) > market_refresh_sec:
            exchanges = await catalog.get_exchanges_snap(key_prefix)
            symbols_cache = {
                ex: list((await catalog.get_symbols_snap(key_prefix, ex)).keys())
                for ex in exchanges.keys()
            }
            last_refresh = now

        for ex, symbols in symbols_cache.items():
            streams = {
                f"{key_prefix}:{STREAM}:{TICKERS}:{ex}:{s}": last_id for s in symbols
            }

            # print("run_ticker_1s_loop streams", streams)
            if not streams:
                continue

            results = await redis.xread(streams, block=1000, count=len(streams) * 5)

            if not results:
                continue

            for stream, messages in results:
                for msg_id, data in messages:
                    last_id = msg_id

                    # print("data", data)
                    payload_raw = data.get(b"p")
                    if not payload_raw:
                        continue

                    payload = json.loads(payload_raw.decode())

                    symbol = payload.get("symbol")
                    price = Decimal(str(payload.get("price", 0)))
                    volume = Decimal(str(payload.get("volume", 0)))
                    ts_open = int(payload.get("timestamp", time.time() * 1000))

                    sec = ts_open // 1000

                    key = f"{ex}:{symbol}"
                    # print("key", key)
                    state = buckets.get(key)
                    # print("state", state)
                    if state is None or state["sec"] != sec:
                        if state:
                            await candle.write_1s(state=state)

                        state = {
                            "sec": sec,
                            "exchange_code": ex,
                            "exchange_symbol": symbol,
                            "open": price,
                            "high": price,
                            "low": price,
                            "close": price,
                            "volume": volume,
                            "ts_open": ts_open,
                        }
                        buckets[key] = state
                    else:
                        state["high"] = max(state["high"], price)
                        state["low"] = min(state["low"], price)
                        state["close"] = price
                        state["volume"] += volume
