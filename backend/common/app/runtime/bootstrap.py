from .settings import settings
from app.core.constants import (
    ExchangeCode,
    CandleInterval,
    SNAP,
    META,
    TICKER,
    CANDLE,
    SYMBOLS,
    EXCHANGES,
)
from app.core import dto as CoreDTO
from app.service.factory import ServiceFactory
from app.facade.container import FacadeContainer
from app.runtime.app_context import (
    WorkerContext,
    WsContext,
    ApiContext,
    DispatcherContext,
    SchedulerContext,
    CollectorContext,
    StreamProcessorContext,
)

# from app.infra.external.rq.queue_factory import RqQueueFactory, RqQueueConfig
# from app.infra.external.rq.worker_factory import RqWorkerFactory, RqWorkerConfig
from app.infra.external.transport.impl.httpx import (
    HttpxSyncTransport,
    HttpxTransportConfig,
)

from app.infra.external.oauth.kakao.provider.oauth import KakaoOAuth
from app.infra.external.oauth.kakao.rest_client import (
    KakaoRestClient,
    KakaoRestClientConfig,
    get_kakao_rest_client,
)

from app.infra.external.redis.provider import (
    RedisActiveMarketCatalogAsync,
    RedisCandleStoreAsync,
    RedisCandleStoreSync,
    RedisCooldown,
    RedisMarketSnapshotPublish,
    RedisState,
)


from app.infra.external.exchange.upbit.shared.types import UpbitWsSubscribe
from app.infra.external.exchange.binance.shared.types import BinanceWsSubscribe
from app.infra.external.exchange.port.ws_client import (
    WsFactoryRegistry,
    WsClient,
)
from app.infra.external.exchange.port.subscribe import SubscribeFactoryRegistry

from app.infra.external.exchange.upbit.provider.symbol import UpbitSymbol
from app.infra.external.exchange.upbit.rest_client import (
    UpbitRestClient,
    UpbitRestClientConfig,
    get_upbit_rest_client,
)
from app.infra.external.exchange.binance.rest_client import (
    BinanceRestClient,
    BinanceRestClientConfig,
    get_binance_rest_client,
)
from app.infra.external.exchange.upbit.ws_client import (
    UpbitWsClient,
    UpbitWsClientConfig,
    get_upbit_ws_client,
)
from app.infra.external.exchange.binance.ws_client import (
    BinanceWsClient,
    BinanceWsClientConfig,
    get_binance_ws_client,
)
from app.infra.external.exchange.binance.provider.symbol import BinanceSymbol
from app.infra.external.redis.async_redis_client import (
    RedisClientAsync,
    get_async_redis_client,
)
from app.infra.external.redis.redis_client import RedisClient, get_redis_client
from app.infra.external.email.ses_client import SesEmailClient
from app.infra.external.email.jinja_renderer import JinjaEmailRenderer
from app.infra.db.uow import UnitOfWork
from app.infra.db.engine import create_sqlalchemy_engine, create_sessionmaker
from app.infra.external.password.passlib_hasher import PasslibPasswordHasher
from app.infra.external.token.jwt_signer import JwtTokenSigner
from app.infra.external.token.hmac_hasher import HmacTokenHasher
from app.infra.external.crypto.local_aesgcm import LocalAesGcmCrypto
from app.infra.external.crypto.local_aesgcm_from_secrets import LocalAesGcmFromSecrets


from typing import Callable, Any
from functools import lru_cache
from passlib.context import CryptContext


def _load_master_key_from_aws() -> str:
    import json, base64  # boto3 응답 처리용
    import boto3

    sm = boto3.client("secretsmanager", region_name=settings.AWS_REGION)
    resp = sm.get_secret_value(SecretId=settings.CRYPTO_DATA_ENC_SECRET_ID)

    if "SecretString" in resp and resp["SecretString"] is not None:
        raw = resp["SecretString"]
        # JSON이면 키 추출
        if settings.CRYPTO_DATA_ENC_SECRET_FIELD:
            data = json.loads(raw)
            return str(data[settings.CRYPTO_DATA_ENC_SECRET_FIELD])
        return raw
    # Binary인 경우
    b = base64.urlsafe_b64decode(resp["SecretBinary"])
    return b.decode("utf-8")  # 네 구현이 문자열→키 파싱을 하므로 utf-8 가정


def _resolve_master_key() -> str:
    if settings.CRYPTO_DATA_ENC_SECRET_ID:
        return _load_master_key_from_aws()
    if settings.CRYPTO_DATA_ENC_KEY:
        return settings.CRYPTO_DATA_ENC_KEY
    raise RuntimeError(
        "Secret master key is not configured. "
        "Set CRYPTO_DATA_ENC_KEY or CRYPTO_DATA_ENC_SECRET_ID."
    )


def _build_symbol_provider_registry():
    return {
        ExchangeCode.UPBIT.value: providers.upbit_symbol_provider(),
        ExchangeCode.BINANCE.value: providers.binance_symbol_provider(),
    }


class Providers:
    """
    - provider는 객체 lifecycle을 관리하지 않는다.
    - 객체 생성/캐싱 책임은 factory, wiring에 있다.
    """

    @staticmethod
    def active_catalog_provider(
        prefix: str,
        async_redis_client: RedisClientAsync,
    ) -> Callable[[], RedisActiveMarketCatalogAsync]:
        return lambda: RedisActiveMarketCatalogAsync(
            async_redis_client,
            exchanges_snap_key=f"{prefix}:{SNAP}:{EXCHANGES}",
            exchanges_meta_key=f"{prefix}:{META}:{EXCHANGES}",
            symbols_snap_key_fn=lambda ex: f"{prefix}:{SNAP}:{SYMBOLS}:{ex}",
            symbols_meta_key_fn=lambda ex: f"{prefix}:{META}:{SYMBOLS}:{ex}",
        )

    @staticmethod
    def candle_store_async_provider(
        async_redis_client: RedisClientAsync,
    ) -> Callable[[], RedisCandleStoreAsync]:
        return lambda: RedisCandleStoreAsync(
            async_redis_client,
            symbols_1s_key_fn=lambda ex, symbol: f"{CANDLE}:{CandleInterval.SEC_1.value}:{ex}:{symbol}",
        )

    @staticmethod
    def candle_store_sync_provider() -> Callable[[], RedisCandleStoreSync]:
        return lambda: RedisCandleStoreSync(
            redis=get_redis_client(settings.REDIS_URL),
            symbols_1s_key_fn=lambda ex, symbol: f"{CANDLE}:{CandleInterval.SEC_1.value}:{ex}:{symbol}",
        )

    @staticmethod
    def kakao_oauth_provider() -> Callable[[], KakaoOAuth]:
        config = KakaoRestClientConfig(
            client_id=settings.KAKAO_CLIENT_ID,
            redirect_uri=settings.KAKAO_OAUTH_REDIRECT_URI,
            client_secret=settings.KAKAO_OAUTH_CLIENT_SECRET,
            admin_key=settings.KAKAO_OAUTH_ADMIN_KEY,
        )
        auth_transport = HttpxSyncTransport(
            HttpxTransportConfig(
                base_url=settings.KAKAO_AUTH_REST_BASE_URL,
                timeout_sec=10.0,
            )
        )

        api_transport = HttpxSyncTransport(
            HttpxTransportConfig(
                base_url=settings.KAKAO_API_REST_BASE_URL,
                timeout_sec=10.0,
            )
        )

        return lambda: KakaoOAuth(
            rest_client=get_kakao_rest_client(
                config=config,
                auth_transport=auth_transport,
                api_transport=api_transport,
            )
        )

    @staticmethod
    def kakao_rest_provider() -> Callable[[], KakaoRestClient]:
        config = KakaoRestClientConfig(
            client_id=settings.KAKAO_CLIENT_ID,
            redirect_uri=settings.KAKAO_OAUTH_REDIRECT_URI,
            client_secret=settings.KAKAO_OAUTH_CLIENT_SECRET,
            admin_key=settings.KAKAO_OAUTH_ADMIN_KEY,
        )
        auth_transport = HttpxSyncTransport(
            HttpxTransportConfig(
                base_url=settings.KAKAO_AUTH_REST_BASE_URL,
                timeout_sec=settings.HTTP_TIMEOUT_SEC,
            )
        )

        api_transport = HttpxSyncTransport(
            HttpxTransportConfig(
                base_url=settings.KAKAO_API_REST_BASE_URL,
                timeout_sec=settings.HTTP_TIMEOUT_SEC,
            )
        )

        return lambda: get_kakao_rest_client(
            config, auth_transport=auth_transport, api_transport=api_transport
        )

    @staticmethod
    def upbit_symbol_provider() -> Callable[[], UpbitSymbol]:
        config = UpbitRestClientConfig(
            base_url=settings.UPBIT_REST_BASE_URL,
            timeout_sec=settings.HTTP_TIMEOUT_SEC,
        )
        return lambda: UpbitSymbol(rest_client=get_upbit_rest_client(config))

    @staticmethod
    def binance_symbol_provider() -> Callable[[], BinanceSymbol]:
        config = BinanceRestClientConfig(
            base_url=settings.BINANCE_REST_BASE_URL,
            timeout_sec=settings.HTTP_TIMEOUT_SEC,
        )
        return lambda: BinanceSymbol(rest_client=get_binance_rest_client(config))

    @staticmethod
    def upbit_ws_provider() -> Callable[[], WsClient]:
        config = UpbitWsClientConfig(
            url=settings.UPBIT_WS_URL,
            ping_interval_sec=settings.WS_PING_INTERVAL_SEC,
            close_timeout_sec=settings.WS_CLOSE_TIMEOUT_SEC,
        )
        return lambda: get_upbit_ws_client(config)

    @staticmethod
    def binance_ws_provider() -> Callable[[], WsClient]:
        config = BinanceWsClientConfig(
            url=settings.BINANCE_WS_URL,
            ping_interval_sec=settings.WS_PING_INTERVAL_SEC,
            close_timeout_sec=settings.WS_CLOSE_TIMEOUT_SEC,
        )
        return lambda: get_binance_ws_client(config)

    @staticmethod
    def snapshot_publisher_provider() -> Callable[[], RedisMarketSnapshotPublish]:
        return lambda: RedisMarketSnapshotPublish(
            redis=get_redis_client(settings.REDIS_URL)
        )

    @staticmethod
    def state_provider() -> Callable[[], RedisState]:
        return lambda: RedisState(redis=get_redis_client(settings.REDIS_URL))

    @staticmethod
    def cooldown_provider() -> Callable[[], RedisCooldown]:
        return lambda: RedisCooldown(redis=get_redis_client(settings.REDIS_URL))

    @staticmethod
    def uow_provider(sqlalchemy_url: str) -> Callable[[], UnitOfWork]:
        engine = create_sqlalchemy_engine(sqlalchemy_url)
        SessionLocal = create_sessionmaker(engine)

        def _provide() -> UnitOfWork:
            # owns_session=True 같은 옵션은 네 UnitOfWork 시그니처에 맞춰서
            db_session = SessionLocal()
            return UnitOfWork(db_session, owns_session=True)

        return _provide

    @staticmethod
    def email_client_provider() -> Callable[[], SesEmailClient]:
        return lambda: SesEmailClient(
            region_name=settings.AWS_REGION,
            access_key_id=settings.AWS_ACCESS_KEY_ID,
            secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            from_email=settings.SES_FROM_EMAIL,
            configuration_set=settings.SES_CONFIGURATION_SET,
        )

    @staticmethod
    def email_renderer_provider() -> Callable[[], JinjaEmailRenderer]:
        return lambda: JinjaEmailRenderer()

    @staticmethod
    def password_hasher_provider() -> Callable[[], PasslibPasswordHasher]:
        # 외부 옵션은 전부 settings에서만 읽음
        ctx = CryptContext(
            schemes=settings.PASSLIB_SCHEMES,
            deprecated=settings.PASSLIB_DEPRECATED,
            # argon2 옵션
            argon2__time_cost=settings.ARGON2_TIME_COST,
            argon2__memory_cost=settings.ARGON2_MEMORY_COST,
            argon2__parallelism=settings.ARGON2_PARALLELISM,
            # bcrypt 옵션
            bcrypt__rounds=settings.BCRYPT_ROUNDS,
        )

        return lambda: PasslibPasswordHasher(ctx)

    @staticmethod
    def jwt_signer_provider() -> Callable[[], JwtTokenSigner]:
        return lambda: JwtTokenSigner(
            secret=settings.JWT_SECRET,
            algorithm=settings.JWT_ALG,
            issuer=settings.JWT_ISSUER,
            audience=settings.JWT_AUDIENCE,
            default_minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
            leeway_seconds=settings.JWT_LEEWAY_SECONDS,
        )

    @staticmethod
    def hmac_hasher_provider() -> Callable[[], HmacTokenHasher]:
        return lambda: HmacTokenHasher(
            token_pepper=settings.TOKEN_MASTER_PEPPER,
            fp_pepper=settings.FP_MASTER_PEPPER,
        )

    @staticmethod
    def secret_crypto_provider() -> Callable[[], LocalAesGcmFromSecrets]:
        def _build():
            key = _resolve_master_key()
            inner = LocalAesGcmCrypto(
                master_key=key
            )  # 키 파싱/길이 검증은 내부에서 수행
            return LocalAesGcmFromSecrets(inner)  # 래퍼로 감싸 동일 인터페이스 제공

        return _build

    # @staticmethod
    # def rq_queue_factory_provider() -> Callable[[], RqQueueFactory]:
    #     def _build() -> RqQueueFactory:
    #         redis_client = get_redis_client(settings.REDIS_URL)
    #         redis_conn_provider = redis_client.conn  # callable
    #         cfg = RqQueueConfig()
    #         return RqQueueFactory(redis_conn_provider, cfg=cfg)

    #     return _build

    # @staticmethod
    # def rq_worker_factory_provider() -> Callable[[], RqWorkerFactory]:
    #     def _build() -> RqWorkerFactory:
    #         redis_client = get_redis_client(settings.REDIS_URL)
    #         redis_conn_provider = redis_client.conn  # callable
    #         cfg = RqWorkerConfig()
    #         return RqWorkerFactory(redis_conn_provider, cfg=cfg)

    #     return _build


providers = Providers()


def build_service_config_bag() -> CoreDTO.ServiceConfigBag:
    return CoreDTO.ServiceConfigBag(
        oauth_state_sec=settings.OAUTH_STATE_TTL_SEC,
        email_resend_cooldown_sec=settings.EMAIL_RESEND_COOLDOWN_SEC,
        access_token_minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
        refresh_token_minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES,
        email_token_minutes=settings.EMAIL_TOKEN_EXPIRE_MINUTES,
        crypto_data_kid=settings.CRYPTO_DATA_ENC_KID,
        public_web_base_url=settings.PUBLIC_WEB_BASE_URL,
        public_api_base_url=settings.PUBLIC_API_BASE_URL,
        public_admin_api_base_url=settings.PUBLIC_ADMIN_API_BASE_URL,
        kakao_auth_rest_base_url=settings.KAKAO_AUTH_REST_BASE_URL,
        kakao_api_rest_base_url=settings.KAKAO_API_REST_BASE_URL,
    )


def build_ws_config_bag() -> CoreDTO.WsConfigBag:
    return CoreDTO.WsConfigBag(
        app_name=settings.APP_NAME,
        deploy_env=settings.DEPLOY_ENV,
        log_level=settings.API_LOG_LEVEL or settings.LOG_LEVEL,
    )


def build_api_config_bag() -> CoreDTO.ApiConfigBag:
    return CoreDTO.ApiConfigBag(
        app_name=settings.APP_NAME,
        deploy_env=settings.DEPLOY_ENV,
        log_level=settings.API_LOG_LEVEL or settings.LOG_LEVEL,
        sentry_dsn=settings.SENTRY_DSN,
        sample_rate=settings.SAMPLE_RATE,
        traces_sample_rate=settings.TRACES_SAMPLE_RATE,
        cors_allow_origins=settings.CORS_ALLOW_ORIGINS,
    )


def build_worker_config_bag() -> CoreDTO.WorkerConfigBag:
    return CoreDTO.WorkerConfigBag(
        app_name=settings.APP_NAME,
        deploy_env=settings.DEPLOY_ENV,
        log_level=settings.WORKER_LOG_LEVEL or settings.LOG_LEVEL,
        sentry_dsn=settings.SENTRY_DSN,
        sample_rate=settings.SAMPLE_RATE,
        traces_sample_rate=settings.TRACES_SAMPLE_RATE,
        redis_url=settings.REDIS_URL,
        outbox_poll_limit=settings.OUTBOX_POLL_LIMIT,
        outbox_idle_sleep=settings.OUTBOX_IDLE_SLEEP,
        outbox_retry_delay_sec=settings.OUTBOX_RETRY_DELAY_SEC,
        outbox_send_lock_ttl_sec=settings.OUTBOX_SEND_LOCK_TTL_SEC,
        outbox_concurrency=settings.OUTBOX_CONCURRENCY,
        # redis_stream_alerts=settings.REDIS_STREAM_ALERTS,
        # redis_stream_deliveries=settings.REDIS_STREAM_DELIVERIES,
        worker_jobs=settings.WORKER_JOBS,
    )


def build_dispatcher_config_bag() -> CoreDTO.DispatcherConfigBag:
    return CoreDTO.DispatcherConfigBag(
        app_name=settings.APP_NAME,
        deploy_env=settings.DEPLOY_ENV,
        log_level=settings.DISPATCHER_LOG_LEVEL or settings.LOG_LEVEL,
        sentry_dsn=settings.SENTRY_DSN,
        sample_rate=settings.SAMPLE_RATE,
        traces_sample_rate=settings.TRACES_SAMPLE_RATE,
        redis_url=settings.REDIS_URL,
        outbox_poll_limit=settings.OUTBOX_POLL_LIMIT,
        outbox_idle_sleep=settings.OUTBOX_IDLE_SLEEP,
    )


def build_scheduler_config_bag() -> CoreDTO.SchedulerConfigBag:
    return CoreDTO.SchedulerConfigBag(
        app_name=settings.APP_NAME,
        deploy_env=settings.DEPLOY_ENV,
        log_level=settings.SCHEDULER_LOG_LEVEL or settings.LOG_LEVEL,
        sentry_dsn=settings.SENTRY_DSN,
        sample_rate=settings.SAMPLE_RATE,
        traces_sample_rate=settings.TRACES_SAMPLE_RATE,
        redis_url=settings.REDIS_URL,
        # exchange=settings.SCHEDULER_EXCHANGE,
        cleanup_interval_sec=settings.SCHEDULER_CLEANUP_INTERVAL_SEC,
        sync_interval_sec=settings.SCHEDULER_SYNC_INTERVAL_SEC,
        tickers_interval_sec=settings.SCHEDULER_TICKERS_INTERVAL_SEC,
        trig_interval_sec=settings.SCHEDULER_TRIG_INTERVAL_SEC,
        snapshot_intervals_sec=settings.SCHEDULER_SNAPSHOT_INTERVALS,
        restart_base_backoff_sec=settings.SCHEDULER_RESTART_BASE_BACKOFF_SEC,
        restart_max_backoff_sec=settings.SCHEDULER_RESTART_MAX_BACKOFF_SEC,
        restart_jitter_ratio=settings.SCHEDULER_RESTART_JITTER_RATIO,
        checkpoint_backend=settings.SCHEDULER_CHECKPOINT_BACKEND,
        checkpoint_key_prefix=settings.SCHEDULER_CHECKPOINT_KEY_PREFIX,
        checkpoint_file_path=settings.SCHEDULER_CHECKPOINT_FILE_PATH,
    )


def build_collector_config_bag() -> CoreDTO.CollectorConfigBag:
    return CoreDTO.CollectorConfigBag(
        app_name=settings.APP_NAME,
        deploy_env=settings.DEPLOY_ENV,
        log_level=settings.COLLECTOR_LOG_LEVEL or settings.LOG_LEVEL,
        sentry_dsn=settings.SENTRY_DSN,
        sample_rate=settings.SAMPLE_RATE,
        traces_sample_rate=settings.TRACES_SAMPLE_RATE,
        redis_url=settings.REDIS_URL,
        enable_stream=settings.COLLECTOR_ENABLE_STREAM,
        stream_reconnect_backoff_sec=settings.COLLECTOR_STREAM_RECONNECT_BACKOFF_SEC,
        restart_base_backoff_sec=settings.COLLECTOR_RESTART_BASE_BACKOFF_SEC,
        restart_max_backoff_sec=settings.COLLECTOR_RESTART_MAX_BACKOFF_SEC,
        restart_jitter_ratio=settings.COLLECTOR_RESTART_JITTER_RATIO,
        checkpoint_backend=settings.COLLECTOR_CHECKPOINT_BACKEND,
        checkpoint_key_prefix=settings.COLLECTOR_CHECKPOINT_KEY_PREFIX,
        checkpoint_file_path=settings.COLLECTOR_CHECKPOINT_FILE_PATH,
        enable_backfill=settings.COLLECTOR_ENABLE_BACKFILL,
        backfill_lookback_minutes=settings.COLLECTOR_BACKFILL_LOOKBACK_MINUTES,
    )


def build_stream_processor_config_bag() -> CoreDTO.StreamProcessorConfigBag:
    return CoreDTO.StreamProcessorConfigBag(
        app_name=settings.APP_NAME,
        deploy_env=settings.DEPLOY_ENV,
        log_level=settings.STREAM_PROCESSOR_LOG_LEVEL or settings.LOG_LEVEL,
        sentry_dsn=settings.SENTRY_DSN,
        sample_rate=settings.SAMPLE_RATE,
        traces_sample_rate=settings.TRACES_SAMPLE_RATE,
        enable_stream=settings.STREAM_PROCESSOR_ENABLE_STREAM,
        stream_reconnect_backoff_sec=settings.STREAM_PROCESSOR_STREAM_RECONNECT_BACKOFF_SEC,
        restart_base_backoff_sec=settings.STREAM_PROCESSOR_RESTART_BASE_BACKOFF_SEC,
        restart_max_backoff_sec=settings.STREAM_PROCESSOR_RESTART_MAX_BACKOFF_SEC,
        restart_jitter_ratio=settings.STREAM_PROCESSOR_RESTART_JITTER_RATIO,
        checkpoint_backend=settings.STREAM_PROCESSOR_CHECKPOINT_BACKEND,
        checkpoint_key_prefix=settings.STREAM_PROCESSOR_CHECKPOINT_KEY_PREFIX,
        checkpoint_file_path=settings.STREAM_PROCESSOR_CHECKPOINT_FILE_PATH,
    )


def create_service_factory(prefix: str) -> ServiceFactory:
    return ServiceFactory(
        uow=providers.uow_provider(settings.SQLALCHEMY_URL),
        candle_store=providers.candle_store_sync_provider(),
        snapshot_publisher=providers.snapshot_publisher_provider(),
        state=providers.state_provider(),
        cooldown=providers.cooldown_provider(),
        email_client=providers.email_client_provider(),
        email_renderer=providers.email_renderer_provider(),
        password_hasher=providers.password_hasher_provider(),
        hmac_hasher=providers.hmac_hasher_provider(),
        jwt_signer=providers.jwt_signer_provider(),
        secret_crypto=providers.secret_crypto_provider(),
        symbol_providers=_build_symbol_provider_registry(),
        kakao_oauth=providers.kakao_oauth_provider(),
        config=build_service_config_bag(),
    )


def create_facade_container(prefix: str) -> FacadeContainer:
    async_redis = get_async_redis_client(settings.REDIS_URL)

    return FacadeContainer(
        candle_store=providers.candle_store_async_provider(
            async_redis_client=async_redis
        ),
        active_catalog=providers.active_catalog_provider(
            prefix=prefix, async_redis_client=async_redis
        ),
    )


@lru_cache
def create_ws_context() -> WsContext:
    cfg = build_ws_config_bag()
    facade = create_facade_container(prefix=f"{cfg.app_name}:{cfg.deploy_env}")

    return WsContext(
        config=cfg,
        facade=facade,
    )


@lru_cache
def create_api_context() -> ApiContext:
    cfg = build_api_config_bag()
    svcs = create_service_factory(prefix=f"{cfg.app_name}:{cfg.deploy_env}")
    return ApiContext(config=cfg, svcs=svcs)


@lru_cache
def create_worker_context() -> WorkerContext:
    cfg = build_worker_config_bag()
    svcs = create_service_factory(prefix=f"{cfg.app_name}:{cfg.deploy_env}")
    redis = get_redis_client(settings.REDIS_URL)
    return WorkerContext(config=cfg, svcs=svcs, redis_client=redis)


@lru_cache
def create_dispatcher_context() -> DispatcherContext:
    cfg = build_dispatcher_config_bag()
    svcs = create_service_factory(prefix=f"{cfg.app_name}:{cfg.deploy_env}")
    redis = get_redis_client(settings.REDIS_URL)
    return DispatcherContext(config=cfg, svcs=svcs, redis_client=redis)


@lru_cache
def create_scheduler_context() -> SchedulerContext:
    cfg = build_scheduler_config_bag()
    svcs = create_service_factory(prefix=f"{cfg.app_name}:{cfg.deploy_env}")
    redis = get_redis_client(settings.REDIS_URL)

    return SchedulerContext(config=cfg, svcs=svcs, redis_client=redis)


@lru_cache
def create_collector_context() -> CollectorContext:
    cfg = build_collector_config_bag()
    facade = create_facade_container(prefix=f"{cfg.app_name}:{cfg.deploy_env}")
    async_redis = get_async_redis_client(settings.REDIS_URL)

    subscribe_facs_register: SubscribeFactoryRegistry = {
        ExchangeCode.UPBIT.value: lambda codes: UpbitWsSubscribe(
            channel="candle.1s",
            codes=codes,
            is_only_snapshot=False,
            is_only_realtime=False,
        ),
        ExchangeCode.BINANCE.value: lambda codes: BinanceWsSubscribe(
            streams=[f"{c.lower()}@trade" for c in codes if isinstance(c, str)]
        ),
    }
    ws_facs_register: WsFactoryRegistry = {
        ExchangeCode.UPBIT.value: providers.upbit_ws_provider(),
        ExchangeCode.BINANCE.value: providers.binance_ws_provider(),
    }

    return CollectorContext(
        config=cfg,
        subscribe_facs_register=subscribe_facs_register,
        ws_facs_register=ws_facs_register,
        async_redis_client=async_redis,
        facade=facade,
    )


@lru_cache
def create_stream_processor_context() -> StreamProcessorContext:
    cfg = build_stream_processor_config_bag()
    facade = create_facade_container(prefix=f"{cfg.app_name}:{cfg.deploy_env}")
    async_redis = get_async_redis_client(settings.REDIS_URL)

    return StreamProcessorContext(
        config=cfg,
        facade=facade,
        async_redis_client=async_redis,
    )


# @lru_cache(maxsize=1)
# def get_rq_queue_factory() -> RqQueueFactory:
#     return providers.rq_queue_factory_provider()


# @lru_cache(maxsize=1)
# def get_rq_worker_factory() -> RqWorkerFactory:
#     return providers.rq_worker_factory_provider()

# rq_queue_factory = get_rq_queue_factory()
# rq_worker_factory = get_rq_worker_factory()
