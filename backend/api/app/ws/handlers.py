from fastapi import WebSocket

from app.service.aio.factory import AsyncServiceFactory
from app.ws.hub import Hub
from app.ws.protocols import WsMessageType, WsChannelType


async def handle_message(
    hub: Hub,
    svcs: AsyncServiceFactory,
    conn_id: str,
    ws: WebSocket,
    data: dict,
) -> None:
    msg_type = data.get("type")
    if not msg_type:
        return

    # -------------------------
    # SUBSCRIBE LIST
    # -------------------------
    if msg_type == WsMessageType.SUBSCRIBE_LIST.value:
        channels = data.get("channels", [])

        if not channels:
            await ws.send_json(
                {
                    "type": WsMessageType.ERROR.value,
                    "message": "channels required",
                }
            )
            return

        for channel in channels:
            await hub.subscribe(conn_id, channel)

        return

    # -------------------------
    # UNSUBSCRIBE LIST
    # -------------------------
    if msg_type == WsMessageType.UNSUBSCRIBE_LIST.value:
        channels = data.get("channels", [])

        if not channels:
            return

        for channel in channels:
            await hub.unsubscribe(conn_id, channel)

        return

    # -------------------------
    # SUBSCRIBE (single)
    # -------------------------
    if msg_type == WsMessageType.SUBSCRIBE.value:
        channel_type = data.get("channel_type")

        if not channel_type:
            return

        if channel_type in {
            WsChannelType.CANDLE_LIST.value,
            WsChannelType.TICKER_LIST.value,
        }:
            channels = {
                channel
                for channel in data.get("channels", [])
                if isinstance(channel, str) and channel
            }

            await hub.subscribe_list(
                conn_id=conn_id,
                channel_type=channel_type,
                channels=channels,
            )
            return

        if channel_type in {
            WsChannelType.CANDLE.value,
            WsChannelType.TICKER.value,
        }:
            channel = data.get("channel")

            if not isinstance(channel, str) or not channel:
                return

            await hub.subscribe(
                conn_id=conn_id,
                channel_type=channel_type,
                channel=channel,
            )
            return

        return

    # -------------------------
    # UNSUBSCRIBE (single)
    # -------------------------
    if msg_type == WsMessageType.UNSUBSCRIBE.value:
        channel_type = data.get("channel_type")
        if not channel_type:
            return

        if channel_type in {
            WsChannelType.CANDLE_LIST.value,
            WsChannelType.TICKER_LIST.value,
        }:
            await hub.unsubscribe_list(
                conn_id=conn_id,
                channel_type=channel_type,
            )
            return

        if channel_type in {
            WsChannelType.CANDLE.value,
            WsChannelType.TICKER.value,
        }:
            await hub.unsubscribe(
                conn_id=conn_id,
                channel_type=channel_type,
            )
            return

        return

    # -------------------------
    # PING (optional)
    # -------------------------
    # if msg_type == WsMessageType.PING.value:
    #     await ws.send_json({"type": WsMessageType.PONG.value})
    #     return
