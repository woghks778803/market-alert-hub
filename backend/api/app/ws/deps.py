from functools import lru_cache
from dataclasses import dataclass
from fastapi import Depends, WebSocket

from app.facade.container import FacadeContainer
from app.runtime.app_context import WsContext
from app.runtime.bootstrap import (
    create_ws_context,
)
from app.ws.hub import Hub


@lru_cache(maxsize=1)  # 의미 없지만 실수 방지를 위한 보호막
def get_ws_context() -> WsContext:
    return create_ws_context()


def get_facade(ws: WebSocket) -> FacadeContainer:
    return ws.app.state.ws_facade


def get_hub(ws: WebSocket) -> Hub:
    return ws.app.state.ws_hub
