from fastapi import APIRouter
from . import health, alerts

router = APIRouter(prefix="/admin-api")   # ← 공통 prefix를 여기서
router.include_router(health.router)
router.include_router(alerts.router, tags=["alerts"])

