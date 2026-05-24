import json, asyncio

from app.core import dto as CoreDTO
from app.core.constants import TICKER
from app.service.aio.factory import AsyncServiceFactory
from app.ws.stores import MarketStore
from app.ws.protocols import WsMessageType


async def run_ticker_consumer(app, interval):
    store: MarketStore = app.state.market_store
    svcs: AsyncServiceFactory = app.state.ws_svcs
    config: CoreDTO.WsConfigBag = app.state.ws_config

    exchanges = await svcs.active_catalog.get_exchanges_snap()

    channels: list[str] = []

    for exchange_code, exchange in exchanges.items():
        symbols = await svcs.active_catalog.get_symbols_snap(exchange_code)

        for exchange_symbol, symbol in symbols.items():
            channels.append(
                svcs.candle_store.channel_key(
                    interval_type=interval.value,
                    ex=exchange_code,
                    symbol=exchange_symbol,
                )
            )

    pubsub = await svcs.ticker_store.subscribe(channels)

    while True:
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
                "type": f"{TICKER}",
                "channel": public_channel,
                "data": payload,
            },
        )