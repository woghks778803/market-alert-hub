from re import L, S
from unittest.util import strclass
from urllib.parse import quote_plus, quote
from pydantic import computed_field, field_validator, Field, EmailStr
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Any
from app.core.constants import (
    OutboxEventType,
    EXCHANGES,
    SYMBOLS,
)


class Settings(BaseSettings):

    def __init__(self, **data: Any):
        #  Pylance에 "키워드 가변 인자 받는다"를 알려줘서 경고 제거
        super().__init__(**data)

    # deploy
    APP_NAME: str
    DEPLOY_ENV: str = "dev"
    LOG_LEVEL: str = "INFO"
    PUBLIC_WEB_BASE_URL: str
    PUBLIC_API_BASE_URL: str
    SENTRY_DSN: str
    SAMPLE_RATE: float
    TRACES_SAMPLE_RATE: float

    # --- DB ---
    MYSQL_HOST: str
    MYSQL_PORT: int = 3306
    MYSQL_DATABASE: str
    MYSQL_USER: str
    MYSQL_PASSWORD: str
    MYSQL_TLS_VERIFY: bool = False

    # --- Redis ---
    REDIS_HOST: str = Field(default="redis")
    REDIS_PORT: int = Field(default=6379)
    REDIS_DB: int = Field(default=0)
    REDIS_SSL: bool = False
    REDIS_ACCESS_PRIMARY_KEY: str | None = None
    REDIS_ACCESS_SECONDARY_KEY: str | None = None
    REDIS_CONNECT_TIMEOUT: float
    REDIS_SOCKET_TIMEOUT: float
    REDIS_HEALTH_CHECK_INTERVAL: float
    REDIS_RETRY_ON_TIMEOUT: bool
    REDIS_CLUSTER_ENABLED: bool

    # --- version switch ---
    ACTIVE_JWT_KID: int = 1
    ACTIVE_TOKEN_PEPPER_KID: int = 1
    ACTIVE_FP_PEPPER_KID: int = 1

    # --- JWT ---
    JWT_SECRET: str = "change-me"
    JWT_ALG: str = "HS256"
    JWT_ISSUER: str | None = None
    JWT_AUDIENCE: str | None = None
    JWT_LEEWAY_SECONDS: int = 0
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 10080  # 7일
    EMAIL_TOKEN_EXPIRE_MINUTES: int = 60
    TOKEN_MASTER_PEPPER: str = "TOKEN_MASTER_PEPPER"
    FP_MASTER_PEPPER: str = "FP_MASTER_PEPPER"

    # --- email ---
    EMAIL_RESEND_COOLDOWN_SEC: int = 60

    # --- notice ---
    NOTICE_VIEW_COOLDOWN_SEC: int = 86400

    # --- ip ---
    IP_RATE_COOLDOWN_SEC: int = 600

    # --- OAuth ---
    OAUTH_STATE_TTL_SEC: int = 300

    # --- password ---
    ARGON2_TIME_COST: int = 2
    ARGON2_MEMORY_COST: int = 102_400
    ARGON2_PARALLELISM: int = 8
    BCRYPT_ROUNDS: int = 12

    PASSLIB_SCHEMES: str | list[str] = ["argon2", "bcrypt"]
    PASSLIB_DEPRECATED: str = "auto"

    # --- crypto ---
    CRYPTO_DATA_ENC_KID: int = 1
    CRYPTO_DATA_ENC_KEY: str | None = None
    CRYPTO_DATA_ENC_SECRET_ID: str | None = None
    CRYPTO_DATA_ENC_SECRET_FIELD: str | None = (
        None  # 시크릿이 JSON이면 내부 키명 (예: "key")
    )

    # SES
    AWS_REGION: str = Field(default="ap-northeast-2")
    SES_FROM_EMAIL: EmailStr
    SES_CONFIGURATION_SET: str | None = None  # 없으면 None
    # 네트워크/보안: 기본은 IAM Role 사용 권장. 로컬 개발 시만 키 사용.
    AWS_ACCESS_KEY_ID: str | None = None
    AWS_SECRET_ACCESS_KEY: str | None = None

    # --- API ---
    API_SERVICE_NAME: str = Field(default="api")
    API_LOG_LEVEL: str = Field(default="INFO")
    CORS_ALLOW_ORIGINS: str | list[str] = ["http://localhost:5173"]

    API_DB_POOL_SIZE: int = 1
    API_DB_MAX_OVERFLOW: int = 0

    # --- WS ---
    WS_LOG_LEVEL: str = Field(default="INFO")
    WS_ASYNC_DB_POOL_SIZE: int = 1
    WS_ASYNC_DB_MAX_OVERFLOW: int = 0

    # --- Dispatcher ---
    DISPATCHER_SERVICE_NAME: str = Field(default="dispatcher")
    DISPATCHER_LOG_LEVEL: str = Field(default="INFO")

    DISPATCHER_DB_POOL_SIZE: int = 1
    DISPATCHER_DB_MAX_OVERFLOW: int = 0

    OUTBOX_POLL_LIMIT: int = Field(default=100)
    OUTBOX_IDLE_SLEEP: float = Field(default=0.5)

    # --- Worker ---
    WORKER_SERVICE_NAME: str = Field(default="worker")
    WORKER_LOG_LEVEL: str = Field(default="INFO")

    WORKER_DB_POOL_SIZE: int = 1
    WORKER_DB_MAX_OVERFLOW: int = 0
    
    OUTBOX_EVENT_BATCH_SIZE: int = Field(default=100)
    OUTBOX_EVENT_BLOCK_MS: int = Field(default=1000)
    OUTBOX_RETRY_DELAY_SEC: int = Field(default=60)
    OUTBOX_SEND_LOCK_TTL_SEC: int = Field(default=120)
    OUTBOX_CONCURRENCY: int = Field(default=4)

    # markets
    REQUEST_MARKET_BACKFILL_JOB_BATCH_SIZE: int = 1
    REQUEST_MARKET_BACKFILL_API_BATCH_SIZE: int = 1

    # tickers
    SYNC_TICKERS_BATCH_SIZE: int = 500

    # exchanges
    SYNC_EXCHANGES_BATCH_SIZE: int = 500
    SYNC_EXCHANGES_TTL_SEC: int = 600

    # symbols
    SYNC_SYMBOLS_BATCH_SIZE: int = 500
    SYNC_SYMBOLS_TTL_SEC: int = 600

    # alerts
    SYNC_ALERTS_BATCH_SIZE: int = 500
    SYNC_ALERTS_TTL_SEC: int = 600
    DISPATCH_ALERT_EVENTS_BATCH_SIZE: int = 500

    # FCM
    FCM_SCOPE: str = "https://www.googleapis.com/auth/firebase.messaging"
    FCM_REST_BASE_URL: str = "https://fcm.googleapis.com"
    FCM_PROJECT_ID: str | None = None
    FCM_SERVICE_ACCOUNT_PATH: str | None = None

    # --- Collector ---
    COLLECTOR_SERVICE_NAME: str = Field(default="collector")
    COLLECTOR_LOG_LEVEL: str = Field(default="INFO")

    COLLECTOR_ENABLE_STREAM: bool = False
    COLLECTOR_STREAM_RECONNECT_BACKOFF_SEC: float = 3.0

    COLLECTOR_RESTART_BASE_BACKOFF_SEC: float = 2.0
    COLLECTOR_RESTART_MAX_BACKOFF_SEC: float = 30.0
    COLLECTOR_RESTART_JITTER_RATIO: float = 0.2

    COLLECTOR_CHECKPOINT_BACKEND: str = "redis"  # memory|file|redis
    COLLECTOR_CHECKPOINT_KEY_PREFIX: str = "collector:checkpoint"
    COLLECTOR_CHECKPOINT_FILE_PATH: str = "/tmp/collector_checkpoint.json"

    COLLECTOR_ENABLE_BACKFILL: bool = False
    COLLECTOR_BACKFILL_LOOKBACK_MINUTES: int = 60

    COLLECTOR_ASYNC_DB_POOL_SIZE: int = 1
    COLLECTOR_ASYNC_DB_MAX_OVERFLOW: int = 0

    # --- Stream Processor ---
    STREAM_PROCESSOR_SERVICE_NAME: str = Field(default="stream_processor")
    STREAM_PROCESSOR_LOG_LEVEL: str = Field(default="INFO")

    STREAM_PROCESSOR_ENABLE_STREAM: bool = False
    STREAM_PROCESSOR_STREAM_RECONNECT_BACKOFF_SEC: float = 3.0

    STREAM_PROCESSOR_RESTART_BASE_BACKOFF_SEC: float = 2.0
    STREAM_PROCESSOR_RESTART_MAX_BACKOFF_SEC: float = 30.0
    STREAM_PROCESSOR_RESTART_JITTER_RATIO: float = 0.2

    STREAM_PROCESSOR_CHECKPOINT_BACKEND: str = "redis"  # memory|file|redis
    STREAM_PROCESSOR_CHECKPOINT_KEY_PREFIX: str = "stream_processor:checkpoint"
    STREAM_PROCESSOR_CHECKPOINT_FILE_PATH: str = "/tmp/stream_processor_checkpoint.json"

    STREAM_PROCESSOR_ASYNC_DB_POOL_SIZE: int = 1
    STREAM_PROCESSOR_ASYNC_DB_MAX_OVERFLOW: int = 0

    ALERT_EVENT_BATCH_SIZE: int = Field(default=100)
    ALERT_EVENT_BLOCK_MS: int = Field(default=1000)
    
    # --- Scheduler ---
    SCHEDULER_SERVICE_NAME: str = Field(default="scheduler")
    SCHEDULER_LOG_LEVEL: str = Field(default="INFO")

    SCHEDULER_RESTART_BASE_BACKOFF_SEC: float = 2.0
    SCHEDULER_RESTART_MAX_BACKOFF_SEC: float = 30.0
    SCHEDULER_RESTART_JITTER_RATIO: float = 0.2

    SCHEDULER_CHECKPOINT_BACKEND: str = "redis"  # memory|file|redis
    SCHEDULER_CHECKPOINT_KEY_PREFIX: str = "scheduler:checkpoint:"
    SCHEDULER_CHECKPOINT_FILE_PATH: str = "/tmp/scheduler_checkpoint.json"

    # Schedule interval
    SCHEDULER_RSS_INTERVAL_SEC: int = 60
    SCHEDULER_CLEANUP_INTERVAL_SEC: int = 86400
    SCHEDULER_EXCHANGES_INTERVAL_SEC: int = 1800
    SCHEDULER_SYMBOLS_INTERVAL_SEC: int = 1800
    SCHEDULER_TICKERS_INTERVAL_SEC: int = 60  # 1분
    SCHEDULER_ALERTS_INTERVAL_SEC: int = 300 # 5분
    SCHEDULER_ALERT_EVENTS_INTERVAL_SEC: int = 10
    SCHEDULER_SNAPSHOT_INTERVALS: list[int] = Field(
        default_factory=lambda: [60, 3600, 86400]
    )

    SCHEDULER_DB_POOL_SIZE: int = 1
    SCHEDULER_DB_MAX_OVERFLOW: int = 0

    # --- network tuning (optional) ---
    HTTP_TIMEOUT_SEC: float = 10.0  # REST 요청 전체 타임아웃
    WS_PING_INTERVAL_SEC: float = 20.0  # WS ping 간격 (None이면 비활성)
    WS_CLOSE_TIMEOUT_SEC: float = 5.0  # WS close 타임아웃

    # --- RSS ---
    RSS_USER_AGENT: str = "market-alert-hub-rss/1.0"
    RSS_SOURCES_BATCH_SIZE: int = 50

    # --- Translation ---
    GOOGLE_TRANSLATION_REST_BASE_URL: str = "https://translation.googleapis.com"
    GOOGLE_TRANSLATE_API_KEY: str
    GOOGLE_TRANSLATE_BATCH_SIZE: int = 50

    # --- Exchange: Binance endpoints (REST/WS) ---
    BINANCE_REST_BASE_URL: str = "https://api.binance.com"  # 업비트 REST API base url
    BINANCE_WS_URL: str = (
        "wss://stream.binance.com:9443/ws"  # 업비트 WebSocket endpoint
    )

    BINANCE_CANDLE_BATCH_SIZE: int = 1000
    BINANCE_CANDLE_RATE_LIMIT: int = 1

    # --- Exchange: Upbit endpoints (REST/WS) ---
    UPBIT_REST_BASE_URL: str = "https://api.upbit.com"  # 업비트 REST API base url
    UPBIT_WS_URL: str = "wss://api.upbit.com/websocket/v1"  # 업비트 WebSocket endpoint

    UPBIT_CANDLE_BATCH_SIZE: int = 200
    UPBIT_CANDLE_RATE_LIMIT: int = 1

    # --- Oauth: Kakao endpoints (REST) ---
    KAKAO_API_REST_BASE_URL: str = "https://kapi.kakao.com"
    KAKAO_AUTH_REST_BASE_URL: str = "https://kauth.kakao.com"

    # --- Kakao network authorize ---
    KAKAO_CLIENT_ID: str
    # KAKAO_ADMIN_KEY

    # --- Oauth: Kakao network authorize
    KAKAO_OAUTH_CLIENT_SECRET: str | None = None
    KAKAO_OAUTH_REDIRECT_URI: str
    KAKAO_OAUTH_ADMIN_KEY: str

    # 로컬 개발 편의: .env 읽기 (컨테이너에선 ENV가 우선)
    model_config = SettingsConfigDict(
        # 환경변수가 없을 때만 주입
        # env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,  # MYSQL_HOST / mysql_host 둘 다 허용
        env_ignore_empty=True, # 빈값이면 무시
        extra="ignore",
    )

    @property
    def WORKER_JOBS(self) -> dict[str, dict[str, Any]]:
        """
        event_type dict로 묶음
        """
        return {
            OutboxEventType.TRANSLATE_NEWS_ITEMS.value: {
                "run_key": OutboxEventType.TRANSLATE_NEWS_ITEMS.value,
                "batch_size": self.GOOGLE_TRANSLATE_BATCH_SIZE,
            },
            OutboxEventType.FETCH_NEWS_FEED.value: {
                "run_key": OutboxEventType.FETCH_NEWS_FEED.value,
                "batch_size": self.RSS_SOURCES_BATCH_SIZE,
            },
            OutboxEventType.DISPATCH_ALERT_EVENTS.value: {
                "run_key": OutboxEventType.DISPATCH_ALERT_EVENTS.value,
                "batch_size": self.DISPATCH_ALERT_EVENTS_BATCH_SIZE,
            },
            OutboxEventType.UNLINK_OAUTH_ACCOUNTS.value: {
                "run_key": OutboxEventType.UNLINK_OAUTH_ACCOUNTS.value,
            },
            OutboxEventType.CLEANUP_DELETED_USERS.value: {
                "run_key": OutboxEventType.CLEANUP_DELETED_USERS.value,
            },
            OutboxEventType.PERSIST_SNAPSHOTS.value: {
                "run_key": OutboxEventType.PERSIST_SNAPSHOTS.value,
            },
            OutboxEventType.REQUEST_MARKET_BACKFILL.value: {
                "run_key": OutboxEventType.REQUEST_MARKET_BACKFILL.value,
                "job_batch_size": self.REQUEST_MARKET_BACKFILL_JOB_BATCH_SIZE,
                "api_batch_size": self.REQUEST_MARKET_BACKFILL_API_BATCH_SIZE,
            },
            OutboxEventType.SYNC_EXCHANGES.value: {
                "run_key": EXCHANGES,
                "batch_size": self.SYNC_EXCHANGES_BATCH_SIZE,
                "ttl_sec": self.SYNC_EXCHANGES_TTL_SEC,
            },
            OutboxEventType.SYNC_SYMBOLS.value: {
                "run_key": SYMBOLS,
                "batch_size": self.SYNC_SYMBOLS_BATCH_SIZE,
                "ttl_sec": self.SYNC_SYMBOLS_TTL_SEC,
            },
            OutboxEventType.SYNC_TICKERS.value: {
                "run_key": OutboxEventType.SYNC_TICKERS.value,
                "batch_size": self.SYNC_TICKERS_BATCH_SIZE,
            },
            OutboxEventType.SYNC_ALERTS.value: {
                "run_key": OutboxEventType.SYNC_ALERTS.value,
                "batch_size": self.SYNC_ALERTS_BATCH_SIZE,
                "ttl_sec": self.SYNC_ALERTS_TTL_SEC,
            },
        }

    @computed_field  # pydantic v2
    @property
    def SQLALCHEMY_URL(self) -> str:
        # URL 비밀번호 인코딩
        pw = quote_plus(self.MYSQL_PASSWORD)  # 특수문자 안전
        return (
            f"mysql+pymysql://{self.MYSQL_USER}:{pw}"
            f"@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DATABASE}"
            f"?charset=utf8mb4"
        )

    @computed_field
    @property
    def SQLALCHEMY_ASYNC_URL(self) -> str:
        pw = quote_plus(self.MYSQL_PASSWORD)
        return (
            f"mysql+asyncmy://{self.MYSQL_USER}:{pw}"
            f"@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DATABASE}"
            f"?charset=utf8mb4"
        )

    @computed_field
    @property
    def REDIS_URL(self) -> str:
        scheme = "rediss" if self.REDIS_SSL else "redis"

        auth = ""
        if self.REDIS_ACCESS_PRIMARY_KEY:
            password = quote(self.REDIS_ACCESS_PRIMARY_KEY, safe="")
            auth = f":{password}@"

        return (
            f"{scheme}://{auth}"
            f"{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        )

    @field_validator("CORS_ALLOW_ORIGINS", "PASSLIB_SCHEMES", mode="before")
    def split_fields(cls, v):
        if isinstance(v, str):
            return [x.strip() for x in v.split(",")]
        return v

    @field_validator("SCHEDULER_SNAPSHOT_INTERVALS", mode="before")
    def parse_snapshot_intervals(cls, v):
        # allow: "60,3600,86400" or [60, 3600, 86400]
        if v is None or v == "":
            return [60, 3600, 86400]

        if isinstance(v, str):
            items = [x.strip() for x in v.split(",") if x.strip()]
            ints = [int(x) for x in items]
        else:
            ints = [int(x) for x in v]

        # validations
        if not ints:
            raise ValueError("SCHEDULER_SNAPSHOT_INTERVALS is empty")

        if any(i <= 0 for i in ints):
            raise ValueError("SCHEDULER_SNAPSHOT_INTERVALS must be positive integers")

        # dedupe + sort
        uniq = sorted(set(ints))
        return uniq


settings = Settings()
