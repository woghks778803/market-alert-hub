from fastapi import APIRouter

from . import auth, markets, supports, users, watchlists, seed, channels, alerts, newses

router = APIRouter(prefix="/api")
router.include_router(auth.router, tags=["Auth"])
router.include_router(users.router, tags=["Users"])
router.include_router(markets.router, tags=["Markets"])
router.include_router(watchlists.router, tags=["Watchlists"])
router.include_router(seed.router, tags=["Seed"])
router.include_router(channels.router, tags=["Channels"])
router.include_router(supports.router, tags=["Support"])
router.include_router(alerts.router, tags=["Alert"])
router.include_router(newses.router, tags=["News"])