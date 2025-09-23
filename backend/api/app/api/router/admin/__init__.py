from fastapi import APIRouter, Depends
from . import health, alerts, auth, users
from app.api.deps import require_admin 

router = APIRouter(
    prefix="/admin-api", 
    dependencies=[Depends(require_admin)]
)
router.include_router(health.router, tags=["Health"])
router.include_router(alerts.router, tags=["Alerts"])
router.include_router(auth.router, tags=["Auth"])
router.include_router(users.router, tags=["Users"])
