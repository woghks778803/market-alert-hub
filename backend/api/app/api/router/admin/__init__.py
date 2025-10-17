from fastapi import APIRouter, Depends, Security
from . import health, alerts, auth, users
from app.api.deps import require_admin 

public = APIRouter(prefix="/admin-api")
public.include_router(auth.router, tags=["Auth"])

protected = APIRouter(prefix="/admin-api", dependencies=[Security(require_admin, scopes=["admin"])])
protected.include_router(users.router, prefix="/users", tags=["Users"])
# router.include_router(health.router, tags=["Health"])
# router.include_router(alerts.router, tags=["Alerts"])
