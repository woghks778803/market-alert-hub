from datetime import datetime
from sqlalchemy import Integer, DateTime, Enum as SAEnum, ForeignKey, SmallInteger, UniqueConstraint, BINARY, LargeBinary, SMALLINT
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.infra.db.base import Base
from app.core.util.datetime import utcnow
from app.core.constants import EmailVerificationStatus  
from app.domain import UserDTO

class EmailVerification(Base):
    __tablename__ = "email_verifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False,
    )

    email_ciphertext: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    email_fingerprint: Mapped[bytes] = mapped_column(BINARY(32), nullable=False)
    email_nonce: Mapped[bytes] = mapped_column(BINARY(12), nullable=False)
    email_key_version: Mapped[int] = mapped_column(SMALLINT, nullable=False) # (unsigned=True)

    token_hash: Mapped[bytes] = mapped_column(BINARY(32), nullable=False)
    status: Mapped[EmailVerificationStatus] = mapped_column(SAEnum(EmailVerificationStatus, values_callable=lambda e: [m.value for m in e],
                                                            native_enum=True, create_constraint=True, validate_strings=True),
                                                            default=EmailVerificationStatus.PENDING, nullable=False)

    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    consumed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    fail_count: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    # user: Mapped["User"] = relationship(back_populates="email_verifications")

    def to_dto(self) -> UserDTO.EmailVerification:
        return UserDTO.EmailVerification(
            id=self.id,
            user_id=self.user_id,
            email_ciphertext=self.email_ciphertext,
            email_fingerprint=self.email_fingerprint,
            email_nonce=self.email_nonce,
            email_key_version=self.email_key_version,
            token_hash=self.token_hash,
            status=self.status,
            expires_at=self.expires_at,
            sent_at=self.sent_at,
            consumed_at=self.consumed_at,
            fail_count=self.fail_count,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )

    @classmethod
    def from_create_dto(cls, dto: UserDTO.EmailVerificationCreate) -> "EmailVerification":

        return cls(
            user_id=dto.user_id,
            email_ciphertext=dto.email_ciphertext,
            email_fingerprint=dto.email_fingerprint,
            email_nonce=dto.email_nonce,
            email_key_version=dto.email_key_version,
            token_hash=dto.token_hash,
            status=EmailVerificationStatus.PENDING,
            expires_at=dto.expires_at,
            sent_at=None,
            consumed_at=None,
            fail_count=0,
        )