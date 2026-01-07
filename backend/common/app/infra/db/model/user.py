from datetime import datetime
from sqlalchemy import Integer, Boolean, String, DateTime, Enum as SAEnum, SMALLINT, BINARY, LargeBinary, func, text, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column
from app.infra.db.base import Base
from app.core.constants import UserRole, UserStatus
from app.core.util.datetime import utcnow
from app.domain import UserDTO

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    email_ciphertext: Mapped[bytes | None] = mapped_column(LargeBinary)
    email_fingerprint: Mapped[bytes | None] = mapped_column(BINARY(32), unique=True)
    email_nonce: Mapped[bytes | None] = mapped_column(BINARY(12))
    email_key_version: Mapped[int | None] = mapped_column(SMALLINT)


    nickname:      Mapped[str] = mapped_column(String(100))
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    role:   Mapped[UserRole] = mapped_column(SAEnum(UserRole, values_callable=lambda e: [m.value for m in e],
                                            native_enum=True, create_constraint=True, validate_strings=True),
                                            nullable=False, default=UserRole.USER, server_default=UserRole.USER)
    status: Mapped[UserStatus] = mapped_column(SAEnum(UserStatus, values_callable=lambda e: [m.value for m in e],
                                            native_enum=True, create_constraint=True, validate_strings=True),
                                            nullable=False, default=UserStatus.ACTIVE, server_default=UserStatus.ACTIVE)

    email_verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=False))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), 
        default=utcnow, 
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), 
        default=utcnow, 
        onupdate=utcnow, 
        nullable=False
    )
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    is_deleted:      Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=text("0"))


    __table_args__ = (
        # ciphertext/nonce/key_version는 셋이 함께 NULL이거나 함께 NOT NULL이어야 함
        CheckConstraint(
            "(email_ciphertext IS NULL AND email_nonce IS NULL AND email_key_version IS NULL) "
            "OR (email_ciphertext IS NOT NULL AND email_nonce IS NOT NULL AND email_key_version IS NOT NULL)",
            name="ck_users_email_crypto_all_or_none"
        ),
    )


    def to_dto(self) -> UserDTO.User:
        return UserDTO.User(
            id=self.id,
            email_ciphertext=self.email_ciphertext,
            email_fingerprint=self.email_fingerprint,
            email_nonce=self.email_nonce,
            email_key_version=self.email_key_version,
            nickname=self.nickname,
            password_hash=self.password_hash,
            role=self.role,
            status=self.status,
            email_verified_at=self.email_verified_at,
            created_at=self.created_at,
            updated_at=self.updated_at,
            last_login_at=self.last_login_at,
            is_deleted=self.is_deleted,
        )