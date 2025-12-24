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
