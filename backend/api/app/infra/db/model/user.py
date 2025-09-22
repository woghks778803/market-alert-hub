from __future__ import annotations
from datetime import datetime
from sqlalchemy import Boolean, String, DateTime, Enum as SAEnum, func, text
from sqlalchemy.orm import Mapped, mapped_column
from app.infra.db.base import Base
from app.core.constants import UserRole, UserStatus


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    email:         Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    nickname:      Mapped[str] = mapped_column(String(100))
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    role:   Mapped[UserRole] = mapped_column(SAEnum(UserRole, native_enum=True, create_constraint=True, validate_strings=True),
                                            nullable=False, default=UserRole.USER, server_default=UserRole.USER)
    status: Mapped[UserStatus] = mapped_column(SAEnum(UserStatus, native_enum=True, create_constraint=True, validate_strings=True),
                                              nullable=False, default=UserStatus.ACTIVE, server_default=UserStatus.ACTIVE)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), 
        server_default=func.now(), 
        default=func.now(), 
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), 
        server_default=func.now(), 
        default=func.now(), 
        onupdate=func.now(), 
        nullable=False
    )
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    is_valid:      Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default=text("1"))