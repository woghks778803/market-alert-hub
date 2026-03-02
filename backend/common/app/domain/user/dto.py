from dataclasses import dataclass
from datetime import datetime
from app.core.constants import UserRole, UserStatus, EmailVerificationStatus


@dataclass(slots=True)
class UserPublicInfo:
    id: int
    email: str | None
    nickname: str
    created_at: datetime
    last_login_at: datetime | None


@dataclass(slots=True)
class UserAdminInfo:
    id: int
    email: str | None
    nickname: str
    created_at: datetime
    last_login_at: datetime | None
    role: str | None = None
    status: str | None = None


@dataclass(slots=True)
class UserEmailInfo:
    id: int
    nickname: str
    email_ciphertext: bytes | None
    email_fingerprint: bytes | None
    email_nonce: bytes | None
    email_key_version: int | None
    email_verified_at: datetime | None


@dataclass(slots=True)
class UserOAuthAccount:
    id: int
    user_id: int
    oauth_providers_id: int
    provider_user_id: str
    linked_at: datetime
    unlinked_at: datetime | None


@dataclass(slots=True)
class UserOAuthAccountCreate:
    user_id: int
    oauth_providers_id: int
    provider_user_id: str
    linked_at: datetime


@dataclass(slots=True)
class OauthProvider:
    id: int
    code: str
    display_name: str
    is_active: bool
    created_at: datetime
    updated_at: datetime


@dataclass(slots=True)
class User:
    id: int
    email_ciphertext: bytes | None
    email_fingerprint: bytes | None
    email_nonce: bytes | None
    email_key_version: int | None
    nickname: str
    password_hash: str | None
    role: UserRole
    status: UserStatus
    email_verified_at: datetime | None
    created_at: datetime
    updated_at: datetime
    last_login_at: datetime | None
    is_deleted: bool
    is_service: bool
    is_privacy: bool
    is_marketing: bool


@dataclass(slots=True)
class UserCreate:
    nickname: str

    is_service: bool
    is_privacy: bool
    is_marketing: bool

    email_ciphertext: bytes | None = None
    email_fingerprint: bytes | None = None
    email_nonce: bytes | None = None
    email_key_version: int | None = None

    password_hash: str | None = None
    last_login_at: datetime | None = None


@dataclass(slots=True)
class EmailVerification:
    id: int
    user_id: int

    email_ciphertext: bytes
    email_fingerprint: bytes
    email_nonce: bytes
    email_key_version: int

    token_hash: bytes
    status: EmailVerificationStatus

    expires_at: datetime
    sent_at: datetime | None
    consumed_at: datetime | None
    fail_count: int

    created_at: datetime
    updated_at: datetime


@dataclass(slots=True)
class EmailVerificationCreate:
    user_id: int

    email_ciphertext: bytes
    email_fingerprint: bytes
    email_nonce: bytes
    email_key_version: int

    token_hash: bytes
    expires_at: datetime


@dataclass(slots=True)
class PasswordReset:
    id: int
    user_id: int
    token_hash: bytes
    expires_at: datetime
    sent_at: datetime | None
    consumed_at: datetime | None
    created_at: datetime


@dataclass(slots=True)
class PasswordResetCreate:
    user_id: int
    token_hash: bytes
    expires_at: datetime
