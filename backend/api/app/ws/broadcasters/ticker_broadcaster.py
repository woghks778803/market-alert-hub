import asyncio

from app.core.constants import TickerInterval
from app.ws.handlers import Hub
from app.ws.stores import MarketStore
from app.ws.protocols import WsChannelType

async def run_ticker_list_broadcaster(app):
    hub: Hub = app.state.ws_hub
    store: MarketStore = app.state.market_store

    while True:
        await asyncio.sleep(60)

        snapshot = store.ticker_list_snapshot(TickerInterval.HOUR_24.value)
        if not snapshot:
            continue

        await hub.broadcast(
            {
                "type": WsChannelType.TICKER_LIST.value,
                "data": snapshot,
            },
        )


async def run_ticker_broadcaster(app):
    hub: Hub = app.state.ws_hub
    store: MarketStore = app.state.market_store
    config: CoreDTO.WsConfigBag = app.state.ws_config

    while True:
        await asyncio.sleep(60)

        for key in store.get_ticker_data().keys():
            snapshot = store.ticker_snapshot(key)
            if not snapshot:
                continue

            await hub.broadcast(
                {
                    "type": WsChannelType.TICKER.value,
                    "data": snapshot,
                },
            )
