from datetime import datetime
from pydantic import BaseModel, EmailStr, Field
from pydantic.config import ConfigDict


# 공용: from_attributes=True (Pydantic v2)
_model_cfg = ConfigDict(from_attributes=True)

class UserCreatePublic(BaseModel):
    email: EmailStr
    nickname: str = Field(max_length=100)
    password: str = Field(min_length=8, max_length=255)

class UserReadPublic(BaseModel):
    model_config = _model_cfg

    id: int
    email: EmailStr
    nickname: str
    created_at: datetime

class MeRead(BaseModel):
    model_config = _model_cfg

    id: int
    email: EmailStr
    nickname: str
    role: str           # enum 문자열 (예: "user" | "admin")
    status: str         # enum 문자열 (예: "active" | "suspended" | "deleted")
    last_login_at: datetime | None = None
