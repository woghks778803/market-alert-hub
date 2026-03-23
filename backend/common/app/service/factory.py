from typing import Callable, Any
from functools import cached_property

from app.core import dto as CoreDTO
from app.domain.shared.uow import UnitOfWork
from app.domain import EmailPort, CryptoPort, MarketPort, AuthPort, ThrottlePort

from .auth_service import AuthService
from .user_service import UserService
from .alert_service import AlertService
from .market_service import MarketService
from .watchlist_service import WatchlistService
from .channel_service import ChannelService
from .email_service import EmailService
from .outbox_service import OutboxService


# TODO: 서비스가 20개 이상으로 증가할 경우 서비스 팩토리를 각 서비스의 팩토리로 분리 필요
class ServiceFactory:
    def __init__(
        self,
        *,
        uow: Callable[[], UnitOfWork],
        snapshot_publisher: Callable[[], MarketPort.MarketSnapshotPublish],
        state: Callable[[], AuthPort.AuthState],
        cooldown: Callable[[], ThrottlePort.Cooldown],
        email_client: Callable[[], EmailPort.EmailClient],
        email_renderer: Callable[[], EmailPort.EmailTemplateRenderer],
        password_hasher: Callable[[], CryptoPort.PasswordHasher],
        hmac_hasher: Callable[[], CryptoPort.TokenHasher],
        jwt_signer: Callable[[], CryptoPort.TokenSigner],
        secret_crypto: Callable[[], CryptoPort.SecretCrypto],
        kakao_oauth: Callable[[], AuthPort.KakaoOAuth],
        symbol_providers: dict[str, Callable[[], MarketPort.ExchangeSymbol]],
        config: CoreDTO.ServiceConfigBag,
    ) -> None:
        self._uow = uow
        self._snapshot_publisher = snapshot_publisher
        self._state = state
        self._cooldown = cooldown
        self._email_client = email_client
        self._email_renderer = email_renderer
        self._password_hasher = password_hasher
        self._hmac_hasher = hmac_hasher
        self._jwt_signer = jwt_signer
        self._secret_crypto = secret_crypto
        self._kakao_oauth = kakao_oauth
        self._symbol_providers = symbol_providers
        self._config = config

    @cached_property
    def symbol_providers(self):
        return {k: v() for k, v in self._symbol_providers.items()}

    @cached_property
    def snapshot_publisher(self):
        return self._snapshot_publisher()

    @cached_property
    def cooldown(self):
        return self._cooldown()

    @cached_property
    def state(self):
        return self._state()

    @cached_property
    def kakao_oauth(self):
        return self._kakao_oauth()

    @cached_property
    def password(self):
        return self._password_hasher()

    @cached_property
    def secrets(self):
        return self._secret_crypto()

    @cached_property
    def jwt(self):
        return self._jwt_signer()

    @cached_property
    def hmac(self):
        return self._hmac_hasher()

    @cached_property
    def emails(self) -> EmailService:
        return EmailService(
            client=self._email_client,
            renderer=self._email_renderer,
            secrets=self.secrets,
            config=self._config,
        )

    @cached_property
    def watchlists(self) -> WatchlistService:
        return WatchlistService(uow_factory=self._uow)

    @cached_property
    def markets(self) -> MarketService:
        return MarketService(
            uow_factory=self._uow,
            symbol_providers=self.symbol_providers,
            snapshot_publisher=self.snapshot_publisher,
        )

    @cached_property
    def users(self) -> UserService:
        return UserService(
            uow_factory=self._uow,
            kakao_oauth=self.kakao_oauth,
            hmac=self.hmac,
            secrets=self.secrets,
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
            state=self.state,
            cooldown=self.cooldown,
            uow_factory=self._uow,
            kakao_oauth=self.kakao_oauth,
            password=self.password,
            hmac=self.hmac,
            jwt=self.jwt,
            secrets=self.secrets,
            config=self._config,
        )

    @cached_property
    def outboxs(self) -> OutboxService:
        return OutboxService(
            uow_factory=self._uow,
            hmac=self.hmac,
        )
