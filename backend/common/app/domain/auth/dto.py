from dataclasses import dataclass
from datetime import datetime
from app.core.constants import UserRole


@dataclass(slots=True, frozen=True)
class AuthToken:
    refresh_token: str
    access_token: str


@dataclass(slots=True, frozen=True)
class AuthUser:
    access_token: str
    id: int
    role: UserRole = UserRole.USER  #  단일 권한
    email_verified_at: datetime | None = None


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


@dataclass(frozen=True)
class EmailVerificationEnqueueResult:
    email_verification_id: int
    verify_token: str
    expires_at: datetime
    outbox_fingerprint: bytes | None


@dataclass(frozen=True)
class OAuthIdentity:
    provider_user_id: str
    email: str | None = None
    nickname: str | None = None
