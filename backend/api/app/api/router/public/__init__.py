from fastapi import APIRouter

from . import health, auth, markets, meta, watchlists, seed

router = APIRouter(prefix="/api")
# router.include_router(health.router, tags=["Health"])
router.include_router(auth.router, tags=["Auth"])
router.include_router(markets.router, tags=["Markets"])
router.include_router(watchlists.router, tags=["Watchlists"])
router.include_router(seed.router, tags=["Seed"])
# router.include_router(meta.router, tags=["Meta"])