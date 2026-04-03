from fastapi import APIRouter

from . import auth, markets, support, users, watchlists, seed, channels

router = APIRouter(prefix="/api")
router.include_router(auth.router, tags=["Auth"])
router.include_router(users.router, tags=["Users"])
router.include_router(markets.router, tags=["Markets"])
router.include_router(watchlists.router, tags=["Watchlists"])
router.include_router(seed.router, tags=["Seed"])
router.include_router(channels.router, tags=["Channels"])
router.include_router(support.router, tags=["Support"])