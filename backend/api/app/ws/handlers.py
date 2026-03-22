from fastapi import WebSocket

from app.ws.hub import Hub
from app.ws.protocols import WsMessageType


async def handle_message(hub: Hub, conn_id: str, ws: WebSocket, data: dict) -> None:
    msg_type = WsMessageType(data.get("type"))

    if msg_type == WsMessageType.SUBSCRIBE:
        symbol = data.get("symbol")
        if not symbol:
            await ws.send_json(
                {"type": WsMessageType.ERROR.value, "message": "symbol required"}
            )
            return

        await hub.subscribe(conn_id, symbol)
        await ws.send_json({"type": WsMessageType.SUBSCRIBE.value, "symbol": symbol})

    elif msg_type == WsMessageType.UNSUBSCRIBE:
        symbol = data.get("symbol")
        if not symbol:
            return

        await hub.unsubscribe(conn_id, symbol)
        await ws.send_json({"type": WsMessageType.UNSUBSCRIBE.value, "symbol": symbol})
