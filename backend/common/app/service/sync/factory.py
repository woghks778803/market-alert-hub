from typing import Callable
from functools import cached_property

from app.core import dto as CoreDTO
from app.domain.shared.uow import UnitOfWork
from app.domain import (
    EmailPort, CryptoPort, 
    MarketPort, AlertPort, 
    AuthPort, ThrottlePort,
    ChannelPort, NewsPort,
    OutboxPort,
)

from .auth_service import AuthService
from .user_service import UserService
from .alert_service import AlertService
from .market_service import MarketService
from .watchlist_service import WatchlistService
from .channel_service import ChannelService
from .email_service import EmailService
from .outbox_service import OutboxService
from .support_service import SupportService
from .news_service import NewsService

# TODO: 서비스가 20개 이상으로 증가할 경우 서비스 팩토리를 각 서비스의 팩토리로 분리 필요
class ServiceFactory:
    def __init__(
        self,
        *,
        uow: Callable[[], UnitOfWork],

        exchange_symbol_providers: dict[str, Callable[[], MarketPort.ExchangeSymbol]],
        channel_message_providers: dict[str, Callable[[], ChannelPort.ChannelMessage]],

        kakao_oauth: Callable[[], AuthPort.KakaoOAuth],
        google_translation: Callable[[], NewsPort.GoogleTranslation],
        news_feed: Callable[[], NewsPort.NewsFeed],

        candle_store: Callable[[], MarketPort.CandleStore],
        market_snapshot: Callable[[], MarketPort.MarketSnapshot],
        alert_snapshot: Callable[[], AlertPort.AlertSnapshot],
        alert_bucket: Callable[[], AlertPort.AlertBucket],
        outbox_event: Callable[[], OutboxPort.OutboxEvent],

        state: Callable[[], AuthPort.AuthState],
        cooldown: Callable[[], ThrottlePort.Cooldown],

        email_client: Callable[[], EmailPort.EmailClient],
        email_renderer: Callable[[], EmailPort.EmailTemplateRenderer],
        password_hasher: Callable[[], CryptoPort.PasswordHasher],
        hmac_hasher: Callable[[], CryptoPort.TokenHasher],
        jwt_signer: Callable[[], CryptoPort.TokenSigner],
        secret_crypto: Callable[[], CryptoPort.SecretCrypto],
        config: CoreDTO.ServiceConfigBag,
    ) -> None:
        self._uow = uow
        self._exchange_symbol_providers = exchange_symbol_providers
        self._channel_message_providers = channel_message_providers
        self._kakao_oauth = kakao_oauth
        self._google_translation = google_translation
        self._news_feed = news_feed
        self._candle_store = candle_store
        self._market_snapshot = market_snapshot
        self._alert_snapshot = alert_snapshot
        self._alert_bucket = alert_bucket
        self._outbox_event = outbox_event
        self._state = state
        self._cooldown = cooldown
        self._email_client = email_client
        self._email_renderer = email_renderer
        self._password_hasher = password_hasher
        self._hmac_hasher = hmac_hasher
        self._jwt_signer = jwt_signer
        self._secret_crypto = secret_crypto
        self._config = config

    @cached_property
    def exchange_symbol_providers(self):
        return {k: v() for k, v in self._exchange_symbol_providers.items()}

    @cached_property
    def channel_message_providers(self):
        return {k: v() for k, v in self._channel_message_providers.items()}

    @cached_property
    def google_translation(self):
        return self._google_translation()

    @cached_property
    def news_feed(self):
        return self._news_feed()

    @cached_property
    def kakao_oauth(self):
        return self._kakao_oauth()

    @cached_property
    def candle_store(self):
        return self._candle_store()

    @cached_property
    def market_snapshot(self):
        return self._market_snapshot()

    @cached_property
    def alert_snapshot(self):
        return self._alert_snapshot()

    @cached_property
    def alert_bucket(self):
        return self._alert_bucket()

    @cached_property
    def outbox_event(self):
        return self._outbox_event()

    @cached_property
    def cooldown(self):
        return self._cooldown()

    @cached_property
    def state(self):
        return self._state()

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
    def alerts(self) -> AlertService:
        return AlertService(
            uow_factory=self._uow,
            channel_message_providers=self.channel_message_providers,
            alert_snapshot=self.alert_snapshot,
            alert_bucket=self.alert_bucket,
        )

    @cached_property
    def watchlists(self) -> WatchlistService:
        return WatchlistService(uow_factory=self._uow)

    @cached_property
    def markets(self) -> MarketService:
        return MarketService(
            uow_factory=self._uow,
            exchange_symbol_providers=self.exchange_symbol_providers,
            candle_store=self.candle_store,
            market_snapshot=self.market_snapshot,
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
            outbox_event=self.outbox_event,
        )

    @cached_property
    def supports(self) -> SupportService:
        return SupportService(
            uow_factory=self._uow,
            cooldown=self.cooldown,
            config=self._config,
        )

    @cached_property
    def newses(self) -> NewsService:
        return NewsService(
            uow_factory=self._uow,
            google_translation=self.google_translation,
            news_feed=self.news_feed,
            hmac=self.hmac,
        )
