from fastapi import APIRouter, Depends, Security
from app.api.router.admin import auth, users, channels
from app.api.deps import require_admin

public = APIRouter(prefix="/admin-api")
public.include_router(auth.router, tags=["Auth"])

protected = APIRouter(
    prefix="/admin-api", dependencies=[Security(require_admin, scopes=["admin"])]
)
protected.include_router(users.router, prefix="/users", tags=["Users"])
protected.include_router(channels.router, prefix="/channels", tags=["Channels"])
