from fastapi import APIRouter
from .public import router as public_router
from .admin import router as admin_router
import app.api.openapi as OpenApi

api = APIRouter(
    responses=OpenApi.combine(OpenApi.ERR_401, OpenApi.ERR_403, OpenApi.ERR_500)
)
api.include_router(public_router)
api.include_router(admin_router)

__all__ = ["api"]
