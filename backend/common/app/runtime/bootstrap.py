from .settings import settings
from app.core.constants import ExchangeCode
from app.core import dto as CoreDTO
from app.service.factory import ServiceFactory
from app.runtime.app_context import (
    WorkerContext,
    ApiContext,
    DispatcherContext,
    SchedulerContext,
    CollectorContext,
)

# from app.infra.external.rq.queue_factory import RqQueueFactory, RqQueueConfig
# from app.infra.external.rq.worker_factory import RqWorkerFactory, RqWorkerConfig
from app.infra.external.exchange.upbit.shared.types import UpbitWsSubscribe
from app.infra.external.exchange.port.ws_client import (
    WsFactoryRegistry,
    WsClient,
    StreamFactory,
    StreamFactoryRegistry,
)
from app.infra.external.exchange.upbit.provider.symbol import UpbitSymbol
from app.infra.external.exchange.upbit.rest_client import (
    UpbitRestClient,
    UpbitRestClientConfig,
    get_rest_client,
)
from app.infra.external.exchange.upbit.ws_client import (
    UpbitWsClient,
    UpbitWsClientConfig,
    get_ws_client,
)
from app.infra.external.redis.async_redis_client import (
    AsyncRedisClient,
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


class Providers:
    @staticmethod
    def upbit_symbol_provider() -> Callable[[], UpbitSymbol]:
        config = UpbitRestClientConfig()
        return lambda: UpbitSymbol(rest_client=get_rest_client(config))

    @staticmethod
    def upbit_rest_provider() -> Callable[[], UpbitRestClient]:
        config = UpbitRestClientConfig()
        return lambda: get_rest_client(config)

    @staticmethod
    def upbit_ws_provider() -> Callable[[], WsClient]:
        config = UpbitWsClientConfig()
        return lambda: get_ws_client(config)

    @staticmethod
    def redis_provider() -> Callable[[], RedisClient]:
        return lambda: get_redis_client(settings.REDIS_URL)

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
        email_verify_resend_cooldown_sec=settings.EMAIL_VERIFY_RESEND_COOLDOWN_SEC,
        access_token_minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
        crypto_data_kid=settings.CRYPTO_DATA_ENC_KID,
        public_web_base_url=settings.PUBLIC_WEB_BASE_URL,
    )


def build_api_config_bag() -> CoreDTO.ApiConfigBag:
    return CoreDTO.ApiConfigBag(
        app_name=settings.APP_NAME,
        deploy_env=settings.DEPLOY_ENV,
        log_level=settings.LOG_LEVEL,
    )


def build_worker_config_bag() -> CoreDTO.WorkerConfigBag:
    return CoreDTO.WorkerConfigBag(
        app_name=settings.APP_NAME,
        deploy_env=settings.DEPLOY_ENV,
        log_level=settings.WORKER_LOG_LEVEL or settings.LOG_LEVEL,
        redis_url=settings.REDIS_URL,
        outbox_poll_limit=settings.OUTBOX_POLL_LIMIT,
        outbox_idle_sleep=settings.OUTBOX_IDLE_SLEEP,
        outbox_retry_delay_sec=settings.OUTBOX_RETRY_DELAY_SEC,
        outbox_send_lock_ttl_sec=settings.OUTBOX_SEND_LOCK_TTL_SEC,
        outbox_concurrency=settings.OUTBOX_CONCURRENCY,
        redis_stream_alerts=settings.REDIS_STREAM_ALERTS,
        redis_stream_deliveries=settings.REDIS_STREAM_DELIVERIES,
        worker_jobs=settings.WORKER_JOBS,
    )


def build_dispatcher_config_bag() -> CoreDTO.DispatcherConfigBag:
    return CoreDTO.DispatcherConfigBag(
        app_name=settings.APP_NAME,
        deploy_env=settings.DEPLOY_ENV,
        log_level=settings.DISPATCHER_LOG_LEVEL or settings.LOG_LEVEL,
        redis_url=settings.REDIS_URL,
        outbox_poll_limit=settings.OUTBOX_POLL_LIMIT,
        outbox_idle_sleep=settings.OUTBOX_IDLE_SLEEP,
    )


def build_scheduler_config_bag() -> CoreDTO.SchedulerConfigBag:
    return CoreDTO.SchedulerConfigBag(
        app_name=settings.APP_NAME,
        deploy_env=settings.DEPLOY_ENV,
        log_level=settings.SCHEDULER_LOG_LEVEL or settings.LOG_LEVEL,
        redis_url=settings.REDIS_URL,
        # exchange=settings.SCHEDULER_EXCHANGE,
        sync_interval_sec=settings.SCHEDULER_SYNC_INTERVAL_SEC,
        trig_interval_sec=settings.SCHEDULER_TRIG_INTERVAL_SEC,
        snapshot_interval_sec=settings.SCHEDULER_SNAPSHOT_INTERVAL_SEC,
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
        redis_url=settings.REDIS_URL,
        # exchange=settings.COLLECTOR_EXCHANGE,
        # enable_catalog_sync=settings.COLLECTOR_ENABLE_CATALOG_SYNC,
        # catalog_sync_interval_sec=settings.COLLECTOR_CATALOG_SYNC_INTERVAL_SEC,
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


def create_service_factory() -> ServiceFactory:

    return ServiceFactory(
        uow=providers.uow_provider(settings.SQLALCHEMY_URL),
        redis_client=providers.redis_provider(),
        email_client=providers.email_client_provider(),
        email_renderer=providers.email_renderer_provider(),
        password_hasher=providers.password_hasher_provider(),
        hmac_hasher=providers.hmac_hasher_provider(),
        jwt_signer=providers.jwt_signer_provider(),
        secret_crypto=providers.secret_crypto_provider(),
        upbit_symbol=providers.upbit_symbol_provider(),
        config=build_service_config_bag(),
    )


def get_core_services() -> ServiceFactory:
    return create_service_factory()


@lru_cache
def create_api_context() -> ApiContext:
    svcs = get_core_services()
    return ApiContext(config=build_api_config_bag(), svcs=svcs)


@lru_cache
def create_worker_context() -> WorkerContext:
    svcs = get_core_services()
    redis = get_redis_client(settings.REDIS_URL)
    return WorkerContext(
        config=build_worker_config_bag(), svcs=svcs, redis_client=redis
    )


@lru_cache
def create_dispatcher_context() -> DispatcherContext:
    svcs = get_core_services()
    redis = get_redis_client(settings.REDIS_URL)
    return DispatcherContext(
        config=build_dispatcher_config_bag(), svcs=svcs, redis_client=redis
    )


@lru_cache
def create_scheduler_context() -> SchedulerContext:
    svcs = get_core_services()
    redis = get_redis_client(settings.REDIS_URL)
    return SchedulerContext(
        config=build_scheduler_config_bag(), svcs=svcs, redis_client=redis
    )


@lru_cache
def create_collector_context() -> CollectorContext:
    async_redis = get_async_redis_client(settings.REDIS_URL)
    subscribe = UpbitWsSubscribe(
        channel="ticker", codes=["KRW-BTC"], is_only_realtime=True
    )

    def _make_stream_factory(exchange_key: str) -> StreamFactory:
        ws_factory = ws_facs_register[exchange_key]

        # stop_event는 "그냥 전달"만 받는다(타입은 Any로 유지해서 asyncio import 회피)
        async def stream_once(cursor: str | None, stop_event: Any):
            ws = ws_factory()
            async for item in ws.stream_once(
                subscribe=subscribe,
                cursor=cursor,
                stop_event=stop_event,
            ):
                yield item

        return stream_once

    ws_facs_register: WsFactoryRegistry = {
        ExchangeCode.UPBIT.value: providers.upbit_ws_provider(),
    }
    stream_facs_register: StreamFactoryRegistry = {
        ExchangeCode.UPBIT.value: _make_stream_factory(ExchangeCode.UPBIT.value),
    }
    return CollectorContext(
        config=build_collector_config_bag(),
        stream_facs_register=stream_facs_register,
        ws_facs_register=ws_facs_register,
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
