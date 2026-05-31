import asyncio, json

from app.core import dto as CoreDTO
from app.service.aio.factory import AsyncServiceFactory
from app.ws.stores import MarketStore
from app.ws.protocols import WsMessageType, WsChannelType


async def run_candle_consumer(app, interval):
    queue = app.state.candle_queue
    store: MarketStore = app.state.market_store
    svcs: AsyncServiceFactory = app.state.ws_svcs
    config: CoreDTO.WsConfigBag = app.state.ws_config
    
    subscribed_channels = await svcs.markets.get_candle_channels(
        interval.value
    )

    pubsub = await svcs.candle_store.subscribe(list(subscribed_channels))

    last_refresh_at = asyncio.get_running_loop().time()

    while True:
        now = asyncio.get_running_loop().time()

        if now - last_refresh_at >= 5.0:
            desired_channels = await svcs.markets.get_candle_channels(interval.value)

            added_channels = desired_channels - subscribed_channels
            removed_channels = subscribed_channels - desired_channels

            if added_channels:
                await pubsub.subscribe(*added_channels)

            if removed_channels:
                await pubsub.unsubscribe(*removed_channels)

            subscribed_channels = desired_channels
            last_refresh_at = now

        msg = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)

        if not msg:
            await asyncio.sleep(0.05)
            continue

        if msg["type"] != WsMessageType.MESSAGE.value:
            continue

        channel = msg["channel"]
        data = msg["data"]

        if not data:
            continue

        if isinstance(channel, bytes):
            channel = channel.decode()
        if isinstance(data, bytes):
            data = data.decode()

        redis_key_prefix = f"{{{config.key_prefix}}}:"
        if channel.startswith(redis_key_prefix):
            public_channel = channel[len(redis_key_prefix):]
        else:
            public_channel = channel

        try:
            payload = json.loads(data)
        except Exception:
            continue

        store.update_candle(
            public_channel,
            {
                "type": WsChannelType.CANDLE.value,
                "channel": public_channel,
                "data": payload,
            },
        )

        await queue.put(public_channel)
