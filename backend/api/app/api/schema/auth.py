from pydantic import EmailStr

from app.core.constants import UserRole
from app.api.schema.base import ApiResponseModel, ApiRequestModel


class Login(ApiRequestModel):
    email: EmailStr
    password: str


class VerifyToken(ApiRequestModel):
    token: str


class PasswordForgot(ApiRequestModel):
    email: EmailStr


class ChangePasswordIn(ApiRequestModel):
    current_password: str
    new_password: str


class ResetPasswordIn(ApiRequestModel):
    token: str
    new_password: str


class ChangeEmailIn(ApiRequestModel):
    new_email: EmailStr


class OAuthStartIn(ApiRequestModel):
    provider: str
    agree_service: bool
    agree_privacy: bool
    agree_marketing: bool


class SimpleOk(ApiResponseModel):
    ok: bool = True


class TokenOut(ApiResponseModel):
    access_token: str
    token_type: str = "bearer"


class CurrentUser(ApiResponseModel):
    id: int
    role: UserRole
    email_verified: bool
    email_enrolled: bool

    class Config:
        frozen = True  # 불변 객체 (선택)
