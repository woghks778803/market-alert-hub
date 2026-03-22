from fastapi import APIRouter
from .main import router as main_router

ws = APIRouter()
ws.include_router(main_router)

__all__ = ["ws"]
