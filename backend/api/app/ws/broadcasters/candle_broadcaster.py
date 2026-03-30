import asyncio

from app.core.constants import CandleInterval
from app.ws.handlers import Hub
from app.ws.stores import MarketStore


async def run_candle_list_broadcaster(app):
    hub: Hub = app.state.ws_hub
    store: MarketStore = app.state.market_store

    while True:
        await asyncio.sleep(2)

        snapshot = store.candle_list_snapshot(CandleInterval.SEC_1.value)

        # print("candle snapshot", snapshot)
        if not snapshot:
            continue

        await hub.broadcast(
            "candle_list",
            {
                "type": "candle_list",
                "data": snapshot,
            },
        )


async def run_candle_broadcaster(app):
    queue = app.state.candle_queue
    hub: Hub = app.state.ws_hub
    store: MarketStore = app.state.market_store

    while True:
        await asyncio.sleep(0.1)

        key = await queue.get()

        snapshot = store.candle_snapshot(key)
        if not snapshot:
            continue

        # print("key", key)
        await hub.broadcast(key, {"type": "candle", "data": snapshot})
