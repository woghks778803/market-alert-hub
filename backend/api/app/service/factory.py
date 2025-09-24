from typing import Callable
from .uow import UnitOfWork
from .auth_service import AuthService
from .user_service import UserService
from .alert_service import AlertService
from .market_service import MarketService


from app.core import settings

class ServiceFactory:
    def __init__(self, uow: Callable[[], UnitOfWork]) -> None:
        self.uow = uow
    
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