import json, asyncio

from app.core.constants import TickerInterval, TICKER
from app.facade.container import FacadeContainer
from app.ws.stores import MarketStore
from app.ws.protocols import WsMessageType


async def run_ticker_consumer(app):
    store: MarketStore = app.state.market_store
    facade: FacadeContainer = app.state.ws_facade

    pubsub = await facade.ticker_store.subscribe(type=TickerInterval.HOUR_24.value)

    while True:
        msg = await pubsub.get_message(ignore_subscribe_messages=True)

        if not msg:
            await asyncio.sleep(0.5)
            continue
        # async for msg in pubsub.listen():
        if msg["type"] != WsMessageType.PMESSAGE.value:
            continue

        channel = msg["channel"]
        data = msg["data"]
        if not data:
            continue

        if isinstance(channel, bytes):
            channel = channel.decode()
        if isinstance(data, bytes):
            data = data.decode()

        try:
            payload = json.loads(data)
        except Exception:
            continue

        store.update_ticker(
            channel,
            {
                "type": f"{TICKER}",
                "channel": channel,
                "data": payload,
            },
        )
        # await hub.broadcast(
        #     channel,
        #     {"type": TICKER, "channel": channel, "data": payload},
        # )
