from datetime import datetime
from pydantic import EmailStr, Field

from app.core.constants import UserRole, UserStatus, ChannelCode, PlatformType
from app.api.schema.base import ApiResponseModel, ApiRequestModel


class UserChannelIn(ApiRequestModel):
    code: ChannelCode = Field(..., description="채널 코드")
    config: dict = Field(..., description="채널별 인증/설정 정보")


class UserSettingIn(ApiRequestModel):
    is_marketing: bool | None = None
    is_quiet_hours: bool | None = None


class UserIn(ApiRequestModel):
    email: EmailStr
    nickname: str = Field(max_length=100)
    password: str = Field(min_length=8, max_length=255)
    agree_service: bool
    agree_privacy: bool
    agree_marketing: bool


class SimpleOk(ApiResponseModel):
    ok: bool = True


class UserReadPublic(ApiResponseModel):
    id: int
    email: EmailStr
    nickname: str
    created_at: datetime
    is_marketing: bool
    is_quiet_hours: bool
    last_login_at: datetime | None = None
    provider_code: str | None = None
    provider_display_name: str | None = None


class UserReadAdmin(ApiResponseModel):
    id: int
    email: EmailStr
    nickname: str | None = None
    role: UserRole | None = None
    status: UserStatus | None = None
    created_at: datetime
    last_login_at: datetime | None = None
