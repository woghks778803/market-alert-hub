import json, asyncio

from app.core import dto as CoreDTO
from app.core.constants import TICKER
from app.facade.container import FacadeContainer
from app.ws.stores import MarketStore
from app.ws.protocols import WsMessageType


async def run_ticker_consumer(app, interval):
    store: MarketStore = app.state.market_store
    facade: FacadeContainer = app.state.ws_facade
    config: CoreDTO.WsConfigBag = app.state.ws_config

    pubsub = await facade.ticker_store.subscribe(interval_type=interval.value)

    while True:
        msg = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)

        if not msg:
            await asyncio.sleep(0.1)
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
        
        redis_prefix = f"{config.app_name}:{config.deploy_env}:"
        if channel.startswith(redis_prefix):
            public_channel = channel[len(redis_prefix):]
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
                "channel": channel,
                "data": payload,
            },
        )