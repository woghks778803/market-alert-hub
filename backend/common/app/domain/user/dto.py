from dataclasses import dataclass
from datetime import datetime

@dataclass(slots=True)
class UserPublicInfo:
    id: int
    email: str
    nickname: str
    created_at: datetime
    last_login_at: datetime | None

@dataclass(slots=True)
class UserAdminInfo:
    id: int
    email: str
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