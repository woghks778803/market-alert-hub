from uuid import uuid4
from fastapi import WebSocket


async def authenticate(websocket: WebSocket) -> str:
    """
    인증 스텁. 필요 시 헤더/쿠키 검증 로직으로 교체.
    """
    return websocket.headers.get("x-conn-id") or websocket.client.host or str(uuid4())
