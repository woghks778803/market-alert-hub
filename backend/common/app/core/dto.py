from dataclasses import dataclass, field, asdict
from typing import Any, Generic, Iterable, Mapping, Optional, Sequence, TypeVar

# 공용 유틸 --------------------------------------------------------------------

T = TypeVar("T")


@dataclass(slots=True)
class Base:
    """모든 DTO의 최소 베이스. 표준 라이브러리만 사용."""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ConfigBag:
    # 이메일 재전송 쿨다운 초
    email_verify_resend_cooldown_sec: int
    # 토큰/세션 등 서비스용 상수
    access_token_minutes: int
    # 암호화 키 KID (이메일 데이터용)
    crypto_data_kid: int
    # 퍼블릭 웹사이트 기본 URL
    public_web_base_url: str


@dataclass(frozen=True)
class WorkerConfigBag:
    redis_url: str
    log_level: str
    outbox_poll_limit: int
    outbox_idle_sleep: float
    outbox_retry_delay_sec: int
    outbox_send_lock_ttl_sec: int
    outbox_concurrency: int
    redis_stream_alerts: str
    redis_stream_deliveries: str


@dataclass(frozen=True)
class DispatcherConfigBag:
    redis_url: str
    log_level: str
    outbox_poll_limit: int
    outbox_idle_sleep: float


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
