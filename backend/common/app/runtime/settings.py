from re import L, S
from unittest.util import strclass
from urllib.parse import quote_plus
from pydantic import computed_field, field_validator, Field, EmailStr
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Any
from app.core.constants import (
    OutboxEventType,
    ExchangeCode,
    SNAP,
    META,
    SYMBOLS,
    EXCHANGES,
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
    PUBLIC_ADMIN_API_BASE_URL: str
    SENTRY_DSN: str
    SAMPLE_RATE: float
    TRACES_SAMPLE_RATE: float

    # --- DB ---
    MYSQL_HOST: str
    MYSQL_PORT: int = 3306
    MYSQL_DATABASE: str
    MYSQL_USER: str
    MYSQL_PASSWORD: str

    # --- Redis ---
    REDIS_HOST: str = Field(default="redis")
    REDIS_PORT: int = Field(default=6379)
    REDIS_DB: int = Field(default=0)

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
    API_LOG_LEVEL: str = Field(default="INFO")
    CORS_ALLOW_ORIGINS: str | list[str] = ["http://localhost:5173"]

    # --- Dispatcher, Worker ---
    WORKER_LOG_LEVEL: str = Field(default="INFO")
    DISPATCHER_LOG_LEVEL: str = Field(default="INFO")
    OUTBOX_POLL_LIMIT: int = Field(default=100)
    OUTBOX_IDLE_SLEEP: float = Field(default=0.5)
    # --- Worker 전용 ---
    OUTBOX_RETRY_DELAY_SEC: int = Field(default=60)
    OUTBOX_SEND_LOCK_TTL_SEC: int = Field(default=120)
    OUTBOX_CONCURRENCY: int = Field(default=4)

    REDIS_STREAM_ALERTS: str = Field(default="alerts")
    REDIS_STREAM_DELIVERIES: str = Field(default="deliveries")

    # exchanges
    SYNC_EXCHANGES_BATCH_SIZE: int = 500
    SYNC_EXCHANGES_TTL_SEC: int = 600

    # symbols
    SYNC_SYMBOLS_BATCH_SIZE: int = 500
    SYNC_SYMBOLS_TTL_SEC: int = 600

    # --- Collector ---
    COLLECTOR_LOG_LEVEL: str = Field(default="INFO")

    # COLLECTOR_EXCHANGE: str = "upbit"

    # COLLECTOR_ENABLE_CATALOG_SYNC: bool = True
    # COLLECTOR_CATALOG_SYNC_INTERVAL_SEC: int = 21600  # 6h

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

    # --- Stream Processor ---
    STREAM_PROCESSOR_LOG_LEVEL: str = Field(default="INFO")

    STREAM_PROCESSOR_ENABLE_STREAM: bool = False
    STREAM_PROCESSOR_STREAM_RECONNECT_BACKOFF_SEC: float = 3.0

    STREAM_PROCESSOR_RESTART_BASE_BACKOFF_SEC: float = 2.0
    STREAM_PROCESSOR_RESTART_MAX_BACKOFF_SEC: float = 30.0
    STREAM_PROCESSOR_RESTART_JITTER_RATIO: float = 0.2

    STREAM_PROCESSOR_CHECKPOINT_BACKEND: str = "redis"  # memory|file|redis
    STREAM_PROCESSOR_CHECKPOINT_KEY_PREFIX: str = "stream_processor:checkpoint"
    STREAM_PROCESSOR_CHECKPOINT_FILE_PATH: str = "/tmp/stream_processor_checkpoint.json"

    # --- Scheduler ---
    SCHEDULER_LOG_LEVEL: str = Field(default="INFO")

    SCHEDULER_RESTART_BASE_BACKOFF_SEC: float = 2.0
    SCHEDULER_RESTART_MAX_BACKOFF_SEC: float = 30.0
    SCHEDULER_RESTART_JITTER_RATIO: float = 0.2

    SCHEDULER_CHECKPOINT_BACKEND: str = "redis"  # memory|file|redis
    SCHEDULER_CHECKPOINT_KEY_PREFIX: str = "scheduler:checkpoint:"
    SCHEDULER_CHECKPOINT_FILE_PATH: str = "/tmp/scheduler_checkpoint.json"

    # Schedule interval
    SCHEDULER_CLEANUP_INTERVAL_SEC: int = 86400
    SCHEDULER_SYNC_INTERVAL_SEC: int = 1800  # 30분
    SCHEDULER_TICKERS_INTERVAL_SEC: int = 60  # 1분
    SCHEDULER_TRIG_INTERVAL_SEC: int = 3  # 3초
    SCHEDULER_SNAPSHOT_INTERVALS: list[int] = Field(
        default_factory=lambda: [60, 3600, 86400]
    )

    # --- network tuning (optional) ---
    HTTP_TIMEOUT_SEC: float = 10.0  # REST 요청 전체 타임아웃
    WS_PING_INTERVAL_SEC: float = 20.0  # WS ping 간격 (None이면 비활성)
    WS_CLOSE_TIMEOUT_SEC: float = 5.0  # WS close 타임아웃

    # --- Exchange: Binance endpoints (REST/WS) ---
    BINANCE_REST_BASE_URL: str = "https://api.binance.com"  # 업비트 REST API base url
    BINANCE_WS_URL: str = (
        "wss://stream.binance.com:9443/ws"  # 업비트 WebSocket endpoint
    )

    # --- Exchange: Upbit endpoints (REST/WS) ---
    UPBIT_REST_BASE_URL: str = "https://api.upbit.com"  # 업비트 REST API base url
    UPBIT_WS_URL: str = "wss://api.upbit.com/websocket/v1"  # 업비트 WebSocket endpoint

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
        extra="ignore",
    )

    @property
    def WORKER_JOBS(self) -> dict[str, dict[str, Any]]:
        """
        event_type dict로 묶음
        """
        return {
            OutboxEventType.SYNC_TICKERS.value: {
                "run_key": OutboxEventType.SYNC_TICKERS.value,
            },
            OutboxEventType.CLEANUP_DELETED_USERS.value: {
                "run_key": OutboxEventType.CLEANUP_DELETED_USERS.value,
            },
            OutboxEventType.PERSIST_SNAPSHOTS.value: {
                "run_key": OutboxEventType.PERSIST_SNAPSHOTS.value,
            },
            OutboxEventType.SYNC_EXCHANGES.value: {
                "run_key": SYMBOLS,
                "batch_size": self.SYNC_EXCHANGES_BATCH_SIZE,
                "ttl_sec": self.SYNC_EXCHANGES_TTL_SEC,
            },
            OutboxEventType.SYNC_SYMBOLS.value: {
                "run_key": SYMBOLS,
                "batch_size": self.SYNC_SYMBOLS_BATCH_SIZE,
                "ttl_sec": self.SYNC_SYMBOLS_TTL_SEC,
            },
        }

    @computed_field  # pydantic v2
    @property
    def SQLALCHEMY_URL(self) -> str:
        pw = quote_plus(self.MYSQL_PASSWORD)  # 특수문자 안전
        return (
            f"mysql+pymysql://{self.MYSQL_USER}:{pw}"
            f"@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DATABASE}"
            f"?charset=utf8mb4"
        )

    @computed_field
    @property
    def REDIS_URL(self) -> str:
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

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
