from datetime import datetime
from sqlalchemy import String, DateTime, Enum as SAEnum, ForeignKey, SmallInteger, UniqueConstraint, BINARY, LargeBinary, SMALLINT
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.infra.db.base import Base
from app.core.util.datetime import utcnow
from app.core.constants import EmailVerificationStatus  

class EmailVerification(Base):
    __tablename__ = "email_verifications"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False,
    )

    email_ciphertext: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    email_fingerprint: Mapped[bytes] = mapped_column(BINARY(32), unique=True, nullable=False)
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
