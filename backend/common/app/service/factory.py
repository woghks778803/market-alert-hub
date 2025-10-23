from typing import Callable
from functools import cached_property

from .auth_service import AuthService
from .user_service import UserService
from .alert_service import AlertService
from .market_service import MarketService
from .watchlist_service import WatchlistService
from .channel_service import ChannelService
from .email_service import EmailService
from .outbox_service import OutboxService

from app.domain.uow import UnitOfWork
from app.domain import EmailPort, CryptoPort

class ServiceFactory:
    def __init__(
            self, 
            *,
            uow: Callable[[], UnitOfWork],
            email_client: Callable[[], EmailPort.EmailClient],
            email_renderer: Callable[[], EmailPort.EmailTemplateRenderer],
            password_hasher: Callable[[], CryptoPort.PasswordHasher],
            jwt_signer: Callable[[], CryptoPort.TokenSigner],
            secret_crypto: Callable[[], CryptoPort.SecretCrypto],
            jwt_secret: str,
            token_minutes: int,
    ) -> None:
        self.uow = uow
        self.email_client = email_client
        self.email_renderer = email_renderer
        self.password_hasher=password_hasher
        self.jwt_signer=jwt_signer
        self.secret_crypto=secret_crypto
        self.jwt_secret=jwt_secret
        self.token_minutes=token_minutes

    @cached_property
    def secrets(self):
        return self.secret_crypto()

    @cached_property
    def jwt(self):
        # 필요 시마다 새 인스턴스 반환(상태 없음)
        return self.jwt_signer()
    
    @cached_property
    def emails(self) -> EmailService:
        return EmailService(client=self.email_client, renderer=self.email_renderer)

    @cached_property
    def watchlists(self) -> WatchlistService:
        return WatchlistService(uow_factory=self.uow)

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
            jwt_secret=self.jwt_secret,
            token_minutes=self.token_minutes
        )

    @cached_property
    def outboxs(self) -> OutboxService:
        return OutboxService(
            uow_factory=self.uow,
        )
