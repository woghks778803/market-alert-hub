from fastapi import APIRouter
from .public import router as public_router
# from .admin import public as admin_public_router, protected as admin_protected_router
import app.api.openapi as OpenApi

api = APIRouter(
    responses=OpenApi.combine(
        OpenApi.ERR_400, OpenApi.ERR_401, OpenApi.ERR_403, OpenApi.ERR_404, OpenApi.ERR_500
    )
)
api.include_router(public_router)
# api.include_router(admin_public_router)
# api.include_router(admin_protected_router)

__all__ = ["api"]
