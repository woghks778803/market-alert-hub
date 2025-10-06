from typing import Callable
from functools import cached_property

from .uow import UnitOfWork
from .auth_service import AuthService
from .user_service import UserService
from .alert_service import AlertService
from .market_service import MarketService
from .watchlist_service import WatchlistService
from .channel_service import ChannelService
from .email_service import EmailService

from app.infra.external.email.ses_client import SesEmailClient
from app.infra.external.email.jinja_renderer import JinjaEmailRenderer
from app.domain import EmailPort

from app.core.settings import settings

class ServiceFactory:
    def __init__(self, uow: Callable[[], UnitOfWork]) -> None:
        self.uow = uow

    @cached_property
    def email_client(self) -> EmailPort.EmailClient:
        return SesEmailClient()

    @cached_property
    def email_renderer(self) -> EmailPort.EmailTemplateRenderer:
        return JinjaEmailRenderer()
    
    @cached_property
    def emails(self) -> EmailService:
        return EmailService(client=self.email_client(), renderer=self.email_renderer())

    @cached_property
    def watchlists(self) -> WatchlistService:
        return WatchlistService(
            uow_factory=self.uow
        )
    
    @cached_property
    def markets(self) -> MarketService:
        return MarketService(
            uow_factory=self.uow,
        )

    @cached_property
    def users(self) -> UserService:
        return UserService(
            uow_factory=self.uow,
        )
    
    @cached_property
    def channels(self) -> ChannelService:
        return ChannelService(
            uow_factory=self.uow,
        )
    
    @cached_property
    def auths(self) -> AuthService:
        return AuthService(
            uow_factory=self.uow,
            jwt_secret=settings.JWT_SECRET,
            token_minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
        )
    
    