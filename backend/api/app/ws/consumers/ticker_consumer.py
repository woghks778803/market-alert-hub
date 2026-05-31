import json, asyncio

from app.core import dto as CoreDTO
from app.service.aio.factory import AsyncServiceFactory
from app.ws.stores import MarketStore
from app.ws.protocols import WsMessageType, WsChannelType


async def run_ticker_consumer(app, interval):
    store: MarketStore = app.state.market_store
    svcs: AsyncServiceFactory = app.state.ws_svcs
    config: CoreDTO.WsConfigBag = app.state.ws_config

    subscribed_channels = await svcs.markets.get_ticker_channels(
        interval.value
    )

    pubsub = await svcs.ticker_store.subscribe(list(subscribed_channels))

    last_refresh_at = asyncio.get_running_loop().time()

    while True:
        now = asyncio.get_running_loop().time()

        if now - last_refresh_at >= 5.0:
            desired_channels = await svcs.markets.get_ticker_channels(interval.value)

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
            await asyncio.sleep(0.1)
            continue
        # async for msg in pubsub.listen():
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

        store.update_ticker(
            public_channel,
            {
                "type": WsChannelType.TICKER.value,
                "channel": public_channel,
                "data": payload,
            },
        )