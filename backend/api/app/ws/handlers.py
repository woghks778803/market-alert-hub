from fastapi import WebSocket

from app.service.aio.factory import AsyncServiceFactory
from app.ws.hub import Hub
from app.ws.protocols import WsMessageType


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
        channel = data.get("channel")
        if not channel:
            return

        await hub.subscribe(conn_id, channel)
        return

    # -------------------------
    # UNSUBSCRIBE (single)
    # -------------------------
    if msg_type == WsMessageType.UNSUBSCRIBE.value:
        channel = data.get("channel")
        if not channel:
            return

        await hub.unsubscribe(conn_id, channel)
        return

    # -------------------------
    # PING (optional)
    # -------------------------
    # if msg_type == WsMessageType.PING.value:
    #     await ws.send_json({"type": WsMessageType.PONG.value})
    #     return
