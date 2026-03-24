from fastapi import WebSocket

from app.facade.container import FacadeContainer
from app.ws.hub import Hub
from app.ws.protocols import WsMessageType


async def handle_message(
    hub: Hub, facade: FacadeContainer, conn_id: str, ws: WebSocket, data: dict
) -> None:
    msg_type = data.get("type")
    if not msg_type:
        return

    if msg_type == WsMessageType.SUBSCRIBE_LIST:
        symbols = data.get("symbols", [])

        if not symbols:
            await ws.send_json(
                {"type": WsMessageType.ERROR.value, "message": "symbols required"}
            )
            return

        for item in symbols:
            exchange = item.get("exchange")
            symbol = item.get("symbol")

            if not exchange or not symbol:
                continue

            key = f"{exchange}:{symbol}"

            await hub.subscribe(conn_id, key)

            # ✅ snapshot 1회
            snapshot = await facade.candle_store.get_1s(exchange, symbol)

            if snapshot is None:
                continue

            await ws.send_json(
                {
                    "type": WsMessageType.SNAPSHOT.value,
                    "exchange": exchange,
                    "symbol": symbol,
                    "data": snapshot,
                }
            )

        return

    if msg_type == WsMessageType.UNSUBSCRIBE_LIST:
        symbols = data.get("symbols", [])

        for item in symbols:
            exchange = item.get("exchange")
            symbol = item.get("symbol")

            if not exchange or not symbol:
                continue

            key = f"{exchange}:{symbol}"
            await hub.unsubscribe(conn_id, key)

        return
