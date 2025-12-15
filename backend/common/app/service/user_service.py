from typing import Callable
from app.domain.uow import UnitOfWork
from app.infra.db.model import UserModel, EmailVerificationModel
from app.domain import CryptoPort, ValidationAppError, NotFoundError
from datetime import datetime, timezone
from app.core.constants import UserStatus, UserRole, EmailVerificationStatus
from app.core.util.datetime import utcnow


class UserService:
    def __init__(
        self,
        *,
        uow_factory: Callable[[], UnitOfWork],
        hmac: CryptoPort.TokenHasher,
    ) -> None:
        self._uow_factory = uow_factory
        self._hmac = hmac

    def coerce(self, value, EnumClass, target_name):
        if value is None or isinstance(value, EnumClass):
            return value
        try:
            return EnumClass(str(value))
        except ValueError:
            raise ValidationAppError(f"Invalid {target_name}", target=target_name)

    def _ensure_user(self, uow: UnitOfWork, user_id: int):
        user = uow.users.get_by_user_id(user_id)
        if not user:
            raise NotFoundError(
                "User not found", target="user_id"
            )  # 전역핸들러에서 404 매핑되게
        return user
    
    def _ensure_email_verification(self, uow: UnitOfWork, email_verification_id: int):
        email_verification = uow.users.get_email_verification_by_id(email_verification_id)
        if not email_verification:
            raise NotFoundError(
                "EmailVerification not found", target="email_verification_id"
            )  
        return email_verification

    def get_user_by_email(self, email: str) -> UserModel | None:
        with self._uow_factory() as uow:
            return uow.users.get_user_by_email_fingerprint(self._hmac.fp_hash(email))

    def list_users_filter(
        self,
        *,
        status: UserStatus | None,
        role: UserRole | None,
        limit: int,
        offset: int,
    ):
        role = self.coerce(role, UserRole, "role")
        status = self.coerce(status, UserStatus, "status")

        with self._uow_factory() as uow:
            rows = uow.users.list_users_filter(status=status, role=role, limit=limit, offset=offset)
            return rows

    def get_by_user_id(self, *, user_id: int) -> UserModel:
        with self._uow_factory() as uow:
            return self._ensure_user(uow, user_id)

    def get_email_verification_by_id(self, *, email_verification_id: int) -> EmailVerificationModel:
        with self._uow_factory() as uow:
            return self._ensure_email_verification(uow, email_verification_id)
    
    def get_email_verification_by_token_hash(self, *, token_hash: bytes) -> EmailVerificationModel:
        with self._uow_factory() as uow:
            email_verification = uow.users.get_email_verification_by_token_hash(token_hash)
            if not email_verification:
                raise NotFoundError(
                    "EmailVerification not found", target="token_hash"
                )
            return email_verification

    def ensure_user(self, *, user_id: int, role: UserRole | None, status: UserStatus | None):
        role = self.coerce(role, UserRole, "role")
        status = self.coerce(status, UserStatus, "status")

        with self._uow_factory() as uow:
            user = self._ensure_user(uow, user_id)
            if role is not None:
                user.role = role
            if status is not None:
                user.status = status

            uow.commit()
            return user

    def set_email_verification_sent(self, *, email_verification_id: int) -> None:
        now = utcnow()
        with self._uow_factory() as uow:
            email_verification = self._ensure_email_verification(uow, email_verification_id)
            email_verification.status = EmailVerificationStatus.SENT
            email_verification.sent_at = now
            uow.commit()

    def delete_user(self, *, user_id: int) -> None:
        with self._uow_factory() as uow:
            user = self._ensure_user(uow, user_id)
            user.status = UserStatus.DELETED
            if hasattr(user, "is_deleted"):
                user.is_deleted = True
            uow.commit()
