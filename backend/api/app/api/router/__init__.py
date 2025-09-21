from fastapi import APIRouter
from .public import router as public_router
from .admin import router as admin_router

api = APIRouter()
api.include_router(public_router)
api.include_router(admin_router)

__all__ = ["api"]
