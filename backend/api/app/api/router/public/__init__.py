from fastapi import APIRouter

from . import health, auth, markets, meta

router = APIRouter(prefix="/api")
router.include_router(health.router, tags=["health"])
router.include_router(auth.router, tags=["auth"])
router.include_router(markets.router, tags=["markets"])
router.include_router(meta.router, tags=["meta"])