from dataclasses import dataclass, field, asdict
from typing import Any, Generic, Iterable, Mapping, Optional, Sequence, TypeVar
from app.core.error.error_model import ErrorSpec

# 공용 유틸 --------------------------------------------------------------------

T = TypeVar("T")


@dataclass(slots=True)
class Base:
    """모든 DTO의 최소 베이스. 표준 라이브러리만 사용."""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# frozen은 non-frozen 상속 불가
@dataclass(frozen=True)
class BaseConfigBag:
    app_name: str
    deploy_env: str

    @property
    def key_prefix(self) -> str:
        return f"{self.app_name}:{self.deploy_env}"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ServiceConfigBag(BaseConfigBag):
    app_name: str
    deploy_env: str
    
    oauth_state_sec: int
    # 이메일 재전송 쿨다운 초
    email_resend_cooldown_sec: int
    # 공지 조회 쿨다운 초
    notice_view_cooldown_sec: int
    # ip 요청 쿨다운 초
    ip_rate_cooldown_sec: int
    # 토큰/세션 등 서비스용 상수
    refresh_token_minutes: int
    access_token_minutes: int
    email_token_minutes: int
    # 암호화 키 KID (이메일 데이터용)
    crypto_data_kid: int
    # 기본 URL
    public_web_base_url: str
    public_api_base_url: str
    kakao_auth_rest_base_url: str


@dataclass(frozen=True)
class ApiConfigBag(BaseConfigBag):
    app_name: str
    deploy_env: str
    service_name: str
    log_level: str
    pool_size: int
    max_overflow: int

    sentry_dsn: str
    sample_rate: float
    traces_sample_rate: float
    cors_allow_origins: str | list[str]


@dataclass(frozen=True)
class WsConfigBag(BaseConfigBag):
    app_name: str
    deploy_env: str
    log_level: str
    pool_size: int
    max_overflow: int


@dataclass(frozen=True)
class WorkerConfigBag(BaseConfigBag):
    app_name: str
    deploy_env: str
    service_name: str
    log_level: str
    pool_size: int
    max_overflow: int

    sentry_dsn: str
    sample_rate: float
    traces_sample_rate: float

    outbox_event_batch_size: int
    outbox_event_block_ms: int
    outbox_retry_delay_sec: int
    outbox_send_lock_ttl_sec: int
    outbox_concurrency: int

    worker_jobs: dict[str, dict[str, object]]


@dataclass(frozen=True)
class DispatcherConfigBag(BaseConfigBag):
    app_name: str
    deploy_env: str
    service_name: str
    log_level: str
    pool_size: int
    max_overflow: int

    sentry_dsn: str
    sample_rate: float
    traces_sample_rate: float

    outbox_poll_limit: int
    outbox_idle_sleep: float


@dataclass(frozen=True)
class SchedulerConfigBag(BaseConfigBag):
    app_name: str
    deploy_env: str
    service_name: str
    log_level: str
    pool_size: int
    max_overflow: int

    sentry_dsn: str
    sample_rate: float
    traces_sample_rate: float

    redis_url: str

    # exchange
    # exchange: str
    rss_interval_sec: int
    cleanup_interval_sec: int
    exchanges_interval_sec: int
    symbols_interval_sec: int
    tickers_interval_sec: int
    alerts_interval_sec: int
    alert_events_interval_sec: int
    snapshot_intervals_sec: list[int]

    # restart policy (supervisor)
    restart_base_backoff_sec: float
    restart_max_backoff_sec: float
    restart_jitter_ratio: float

    # checkpoint(state)
    checkpoint_backend: str  # memory | file | redis
    checkpoint_key_prefix: str
    checkpoint_file_path: str


@dataclass(frozen=True)
class CollectorConfigBag(BaseConfigBag):
    # 공통
    app_name: str
    deploy_env: str
    service_name: str
    log_level: str
    pool_size: int
    max_overflow: int

    sentry_dsn: str
    sample_rate: float
    traces_sample_rate: float

    redis_url: str

    # 1) catalog sync
    # enable_catalog_sync: bool
    # catalog_sync_interval_sec: int

    # 2) market stream
    enable_stream: bool
    stream_reconnect_backoff_sec: float

    # restart policy (supervisor)
    restart_base_backoff_sec: float
    restart_max_backoff_sec: float
    restart_jitter_ratio: float

    # checkpoint(state)
    checkpoint_backend: str  # memory | file | redis
    checkpoint_key_prefix: str
    checkpoint_file_path: str

    # (optional) backfill
    enable_backfill: bool
    backfill_lookback_minutes: int


@dataclass(frozen=True)
class StreamProcessorConfigBag(BaseConfigBag):
    # 공통
    app_name: str
    deploy_env: str
    service_name: str
    log_level: str
    pool_size: int
    max_overflow: int
    
    sentry_dsn: str
    sample_rate: float
    traces_sample_rate: float

    enable_stream: bool
    stream_reconnect_backoff_sec: float

    restart_base_backoff_sec: float
    restart_max_backoff_sec: float
    restart_jitter_ratio: float

    checkpoint_backend: str  # memory | file | redis
    checkpoint_key_prefix: str
    checkpoint_file_path: str

    alert_event_batch_size: int
    alert_event_block_ms: int


# 페이징/정렬 -------------------------------------------------------------------


@dataclass(slots=True)
class Sort(Base):
    field: str
    direction: str = "asc"  # "asc" | "desc"


@dataclass(slots=True)
class Page(Base, Generic[T]):
    items: Sequence[T]
    total: int
    page: int
    size: int
    sort: Optional[Sort] = None


# ---------------------------------------------------
@dataclass
class HandlerResult:
    success: bool
    retryable: bool
    result_code: str
    result_message: str | None
    result_payload: dict
    spec: ErrorSpec | None = None
