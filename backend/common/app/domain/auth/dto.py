from dataclasses import dataclass
from app.core.constants import UserRole


@dataclass(slots=True, frozen=True)
class AuthToken:
    access_token: str


@dataclass(slots=True, frozen=True)
class AuthUser:
    access_token: str
    id: int
    role: UserRole = UserRole.USER  #  단일 권한

@dataclass(slots=True)
class Session:
    id: int
    user_id: int
    token_hash: bytes
    user_agent: str | None
    ip_addr: str | None
    created_at: datetime
    expires_at: datetime
    revoked_at: datetime | None

    
