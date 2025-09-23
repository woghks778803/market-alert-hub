from datetime import datetime
from pydantic import BaseModel, EmailStr, Field
from pydantic.config import ConfigDict
from app.core.constants import UserRole, UserStatus

# 공용: from_attributes=True (Pydantic v2)
_model_cfg = ConfigDict(from_attributes=True, use_enum_values=True)

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
    status: UserStatus | None = Field(default=None, description="active|suspended|deleted")

class MeRead(BaseModel):
    model_config = _model_cfg

    id: int
    email: EmailStr
    nickname: str
    role: UserRole | None = Field(default=None, description="user|admin")
    status: UserStatus | None = Field(default=None, description="active|suspended|deleted") 
    last_login_at: datetime | None = None
