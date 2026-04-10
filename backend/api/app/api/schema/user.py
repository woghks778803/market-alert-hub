from datetime import datetime
from pydantic import BaseModel, EmailStr, Field
from pydantic.config import ConfigDict
from app.core.constants import UserRole, UserStatus, ChannelCode, PlatformType

_model_cfg = ConfigDict(from_attributes=True, use_enum_values=True)

class SimpleOk(BaseModel):
    ok: bool = True

class UserSettingIn(BaseModel):
    is_marketing: bool | None = None
    is_quiet_hours: bool | None = None

class UserCreateIn(BaseModel):
    email: EmailStr
    nickname: str = Field(max_length=100)
    password: str = Field(min_length=8, max_length=255)
    agree_service: bool
    agree_privacy: bool
    agree_marketing: bool


class UserReadPublic(BaseModel):
    model_config = _model_cfg

    id: int
    email: EmailStr
    nickname: str
    created_at: datetime
    is_marketing: bool
    is_quiet_hours: bool
    last_login_at: datetime | None = None
    provider_code: str | None = None
    provider_display_name: str | None = None


class UserReadAdmin(BaseModel):
    model_config = _model_cfg

    id: int
    email: EmailStr
    nickname: str | None = None
    role: UserRole | None = None
    status: UserStatus | None = None
    created_at: datetime
    last_login_at: datetime | None = None


class UserUpdateAdmin(BaseModel):
    role: UserRole | None = Field(default=None, description="user|admin")
    status: UserStatus | None = Field(
        default=None, description="active|suspended|deleted"
    )

class UserChannelIn(BaseModel):
    code: ChannelCode = Field(..., description="채널 코드")
    config: dict = Field(..., description="채널별 인증/설정 정보")