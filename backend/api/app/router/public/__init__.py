# app/router/admin/__init__.py
from fastapi import APIRouter
from . import health, auth

router = APIRouter(prefix="/admin-api")
router.include_router(health.router, tags=["health"])
router.include_router(auth.router, tags=["auth"])
