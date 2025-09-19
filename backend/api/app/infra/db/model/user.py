from __future__ import annotations
import enum
from datetime import datetime
from sqlalchemy import String, DateTime, Enum as SAEnum, func
from sqlalchemy.orm import Mapped, mapped_column
from app.infra.db.base import Base

class UserRole(str, enum.Enum):
    user  = "user"
    admin = "admin"

class UserStatus(str, enum.Enum):
    active    = "active"
    suspended = "suspended"
    deleted   = "deleted"

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    email:         Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    nickname:      Mapped[str] = mapped_column(String(100))
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    role:   Mapped[UserRole] = mapped_column(SAEnum(UserRole, native_enum=False, create_constraint=True, validate_strings=True),
                                            nullable=False, default=UserRole.user)
    status: Mapped[UserStatus] = mapped_column(SAEnum(UserStatus, native_enum=False, create_constraint=True, validate_strings=True),
                                              nullable=False, default=UserStatus.active)

    created_at:    Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    last_login_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
