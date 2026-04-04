from pydantic import BaseModel, EmailStr
from app.core.constants import UserRole


class Login(BaseModel):
    email: EmailStr
    password: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


class SimpleOk(BaseModel):
    ok: bool = True


class VerifyToken(BaseModel):
    token: str


class PasswordForgot(BaseModel):
    email: EmailStr


class ChangePasswordIn(BaseModel):
    current_password: str
    new_password: str

class ResetPasswordIn(BaseModel):
    token: str
    new_password: str


class ChangeEmailIn(BaseModel):
    new_email: EmailStr


class OAuthStartIn(BaseModel):
    provider: str
    agree_service: bool
    agree_privacy: bool
    agree_marketing: bool


class CurrentUser(BaseModel):
    id: int
    role: UserRole
    email_verified: bool | None = None

    class Config:
        frozen = True  # 불변 객체 (선택)
