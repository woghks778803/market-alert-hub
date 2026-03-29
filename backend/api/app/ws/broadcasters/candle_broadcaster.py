import asyncio

from app.ws.handlers import Hub
from app.ws.stores import MarketStore


async def run_candle_list_broadcaster(app):
    hub: Hub = app.state.ws_hub
    store: MarketStore = app.state.market_store

    while True:
        await asyncio.sleep(2)

        snapshot = store.candle_list_snapshot()

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
    hub: Hub = app.state.ws_hub
    store: MarketStore = app.state.market_store

    while True:
        await asyncio.sleep(1)

        for key in store.get_candle_data().keys():
            # BINANCE:BTCUSDT
            snapshot = store.candle_snapshot(key)

            # print("candle snapshot", snapshot)
            if not snapshot:
                continue

            await hub.broadcast(
                key,
                {
                    "type": "candle",
                    "data": snapshot,
                },
            )
