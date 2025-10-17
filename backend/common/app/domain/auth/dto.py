from dataclasses import dataclass
from app.core.constants import UserRole

@dataclass(slots=True, frozen=True)
class AuthToken:
    access_token: str

@dataclass(slots=True, frozen=True)
class AuthUser:
    id: int
    email: str | None = None
    role: UserRole = UserRole.USER  # ✅ 단일 권한