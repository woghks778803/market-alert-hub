from fastapi import APIRouter

from app.api.router.public import auth, markets, supports, users, watchlists, seed, alerts, newses

router = APIRouter(prefix="/api")
router.include_router(auth.router, tags=["Auth"])
router.include_router(users.router, tags=["Users"])
router.include_router(markets.router, tags=["Markets"])
router.include_router(watchlists.router, tags=["Watchlists"])
router.include_router(supports.router, tags=["Supports"])
router.include_router(alerts.router, tags=["Alerts"])
router.include_router(newses.router, tags=["Newses"])
router.include_router(seed.router, tags=["Seed"])