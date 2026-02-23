from pydantic import BaseModel, EmailStr


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
    token: str
    current_password: str
    new_password: str


class ChangeEmailIn(BaseModel):
    current_password: str
    new_email: EmailStr
