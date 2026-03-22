from functools import lru_cache
from dataclasses import dataclass
from fastapi import Depends, Request

from app.runtime.app_context import WsContext
from app.runtime.bootstrap import (
    create_ws_context,
)
from app.ws.hub import Hub


@lru_cache(maxsize=1)  # 의미 없지만 실수 방지를 위한 보호막
def get_app_context() -> WsContext:
    return create_ws_context()


def get_candle_store(
    ctx: WsContext = Depends(get_app_context),
):
    return ctx.candle_store


def get_hub(request: Request) -> Hub:
    return request.app.state.ws_hub
