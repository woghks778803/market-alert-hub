from fastapi import APIRouter

from . import health, auth, markets, meta

router = APIRouter(prefix="/api")
router.include_router(health.router, tags=["Health"])
router.include_router(auth.router, tags=["Auth"])
router.include_router(markets.router, tags=["Markets"])
router.include_router(meta.router, tags=["Meta"])