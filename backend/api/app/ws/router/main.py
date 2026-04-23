import uuid

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends

from app.service.aio.factory import AsyncServiceFactory
from app.ws.deps import get_hub, get_services
from app.ws.handlers import handle_message
from app.ws.hub import Hub
from app.ws.protocols import WsMessageType

router = APIRouter(prefix="/ws")


@router.websocket("")
async def websocket_endpoint(
    ws: WebSocket,
    hub: Hub = Depends(get_hub),
    svcs: AsyncServiceFactory = Depends(get_services),
) -> None:
    await ws.accept()
    conn_id = str(uuid.uuid4())

    await hub.register(conn_id, ws)
    await ws.send_json({"type": WsMessageType.INIT.value})

    try:
        while True:
            data = await ws.receive_json()
            await handle_message(hub, svcs, conn_id, ws, data)

    except WebSocketDisconnect:
        pass

    finally:
        await hub.unregister(conn_id)
