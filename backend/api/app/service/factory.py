from typing import Callable
from .uow import UnitOfWork
from .auth_service import AuthService
from .user_service import UserService
from .alert_service import AlertService
from .market_service import MarketService
from .watchlist_service import WatchlistService


from app.core.settings import settings

class ServiceFactory:
    def __init__(self, uow: Callable[[], UnitOfWork]) -> None:
        self.uow = uow

    def watchlists(self) -> WatchlistService:
        return WatchlistService(
            uow_factory=self.uow
        )
    
    def markets(self) -> MarketService:
        return MarketService(
            uow_factory=self.uow,
        )

    def users(self) -> UserService:
        return UserService(
            uow_factory=self.uow,
        )
    
    def auths(self) -> AuthService:
        return AuthService(
            uow_factory=self.uow,
            jwt_secret=settings.JWT_SECRET,
            token_minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
        )