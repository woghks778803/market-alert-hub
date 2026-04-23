import asyncio, json

from app.core import dto as CoreDTO
from app.core.constants import CANDLE
from app.service.aio.factory import AsyncServiceFactory
from app.ws.stores import MarketStore
from app.ws.protocols import WsMessageType


async def run_candle_consumer(app, interval):
    queue = app.state.candle_queue
    store: MarketStore = app.state.market_store
    svcs: AsyncServiceFactory = app.state.ws_svcs
    config: CoreDTO.WsConfigBag = app.state.ws_config

    pubsub = await svcs.candle_store.subscribe(interval_type=interval.value)

    while True:
        msg = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)

        if not msg:
            await asyncio.sleep(0.05)
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

        redis_prefix = f"{config.app_name}:{config.deploy_env}:"
        if channel.startswith(redis_prefix):
            public_channel = channel[len(redis_prefix):]
        else:
            public_channel = channel

        try:
            payload = json.loads(data)
        except Exception:
            continue

        store.update_candle(
            public_channel,
            {
                "type": f"{CANDLE}",
                "channel": channel,
                "data": payload,
            },
        )

        await queue.put(public_channel)
