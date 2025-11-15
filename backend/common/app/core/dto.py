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
    # 토큰/세션 등 서비스용 상수
    access_token_minutes: int
    # 암호화 키 KID (이메일 데이터용)
    crypto_data_kid: int

# 페이징/정렬 -------------------------------------------------------------------

@dataclass(slots=True)
class Sort(Base):
    field: str
    direction: str = "asc"   # "asc" | "desc"

@dataclass(slots=True)
class Page(Base, Generic[T]):
    items: Sequence[T]
    total: int
    page: int
    size: int
    sort: Optional[Sort] = None

