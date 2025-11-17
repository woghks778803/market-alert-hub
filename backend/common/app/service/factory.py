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
from app.core import dto as CoreDTO

class ServiceFactory:
    def __init__(
        self,
        *,
        uow: Callable[[], UnitOfWork],
        email_client: Callable[[], EmailPort.EmailClient],
        email_renderer: Callable[[], EmailPort.EmailTemplateRenderer],
        password_hasher: Callable[[], CryptoPort.PasswordHasher],
        hmac_hasher: Callable[[], CryptoPort.TokenHasher],
        jwt_signer: Callable[[], CryptoPort.TokenSigner],
        secret_crypto: Callable[[], CryptoPort.SecretCrypto],
        config : CoreDTO.ConfigBag,
    ) -> None:
        self._trace_id: str | None = None
        self._uow = uow
        self._email_client = email_client
        self._email_renderer = email_renderer
        self._password_hasher = password_hasher
        self._hmac_hasher = hmac_hasher
        self._jwt_signer = jwt_signer
        self._secret_crypto = secret_crypto
        self._config = config 

    @cached_property
    def password(self):
        return self._password_hasher()

    @cached_property
    def secrets(self):
        return self._secret_crypto()

    @cached_property
    def jwt(self):
        # 필요 시마다 새 인스턴스 반환(상태 없음)
        return self._jwt_signer()

    @cached_property
    def hmac(self):
        # 필요 시마다 새 인스턴스 반환(상태 없음)
        return self._hmac_hasher()

    @cached_property
    def emails(self) -> EmailService:
        return EmailService(client=self._email_client, renderer=self._email_renderer)

    @cached_property
    def watchlists(self) -> WatchlistService:
        return WatchlistService(uow_factory=self._uow)

    @cached_property
    def markets(self) -> MarketService:
        return MarketService(
            uow_factory=self._uow,
        )

    @cached_property
    def users(self) -> UserService:
        return UserService(
            uow_factory=self._uow,
            hmac=self.hmac,
        )

    @cached_property
    def channels(self) -> ChannelService:
        return ChannelService(
            uow_factory=self._uow,
            hmac=self.hmac,
        )

    @cached_property
    def auths(self) -> AuthService:
        return AuthService(
            trace_id=self._trace_id,
            uow_factory=self._uow,
            password=self.password,
            hmac=self.hmac,
            jwt=self.jwt,
            secrets=self.secrets,
            config=self._config,
        )

    @cached_property
    def outboxs(self) -> OutboxService:
        return OutboxService(
            trace_id=self._trace_id,
            uow_factory=self._uow,
        )
