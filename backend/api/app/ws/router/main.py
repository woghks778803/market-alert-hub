import uuid

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends

from app.ws.deps import get_hub, get_app_context
from app.ws.handlers import handle_message
from app.ws.hub import Hub

router = APIRouter()


@router.websocket("")
async def websocket_endpoint(
    ws: WebSocket,
    hub: Hub = Depends(get_hub),
) -> None:
    await ws.accept()
    conn_id = str(uuid.uuid4())
    await hub.register(conn_id, ws)

    try:
        while True:
            data = await ws.receive_json()
            await handle_message(hub, conn_id, ws, data)

    except WebSocketDisconnect:
        pass

    finally:
        await hub.unregister(conn_id)
