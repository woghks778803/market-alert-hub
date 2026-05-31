import asyncio

from app.core.constants import CandleInterval
from app.ws.handlers import Hub
from app.ws.stores import MarketStore
from app.ws.protocols import WsChannelType

async def run_candle_list_broadcaster(app):
    hub: Hub = app.state.ws_hub
    store: MarketStore = app.state.market_store

    while True:
        await asyncio.sleep(2)

        snapshot = store.candle_list_snapshot(CandleInterval.SEC_1.value)

        if not snapshot:
            continue

        await hub.broadcast(
            {
                "type": WsChannelType.CANDLE_LIST.value,
                "data": snapshot,
            },
        )


async def run_candle_broadcaster(app):
    queue = app.state.candle_queue
    hub: Hub = app.state.ws_hub
    store: MarketStore = app.state.market_store
    config: CoreDTO.WsConfigBag = app.state.ws_config

    while True:
        await asyncio.sleep(0)

        key = await queue.get()
        snapshot = store.candle_snapshot(key)

        if not snapshot:
            continue

        await hub.broadcast(
            {
                "type": WsChannelType.CANDLE.value, 
                "data": snapshot
            }
        )
