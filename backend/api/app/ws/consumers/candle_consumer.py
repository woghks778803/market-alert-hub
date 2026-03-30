import asyncio, json

from app.core.constants import CANDLE
from app.facade.container import FacadeContainer
from app.ws.stores import MarketStore
from app.ws.protocols import WsMessageType


async def run_candle_consumer(app, interval):
    queue = app.state.candle_queue
    store: MarketStore = app.state.market_store
    facade: FacadeContainer = app.state.ws_facade

    pubsub = await facade.candle_store.subscribe(type=interval.value)

    while True:
        msg = await pubsub.get_message(ignore_subscribe_messages=True)

        if not msg:
            await asyncio.sleep(0.1)
            continue

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

        store.update_candle(
            channel,
            {
                "type": f"{CANDLE}",
                "channel": channel,
                "data": payload,
            },
        )

        await queue.put(channel)
