from typing import Callable, Any
from app.core.util.datetime import (
    utcnow,
)
from app.core.constants import UserStatus, UserRole, EmailVerificationStatus
from app.domain.shared.uow import UnitOfWork
from app.domain.shared.errors import (
    ValidationAppError,
    NotFoundError,
    AuthError
)
from app.domain import UserDTO, EmailDTO, CryptoPort, AuthPort


class UserService:
    def __init__(
        self,
        *,
        uow_factory: Callable[[], UnitOfWork],
        kakao_oauth: AuthPort.KakaoOAuth,
        hmac: CryptoPort.TokenHasher,
        secrets: CryptoPort.SecretCrypto,
    ) -> None:
        self._uow_factory = uow_factory
        self._kakao_oauth = kakao_oauth
        self._hmac = hmac
        self._secrets = secrets

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
        email_verification = uow.users.get_email_verification_by_id(
            email_verification_id
        )
        if not email_verification:
            raise NotFoundError(
                "EmailVerification not found", target="email_verification_id"
            )
        return email_verification

    def _ensure_password_reset(
        self, uow: UnitOfWork, password_reset_id: int
    ) -> UserDTO.PasswordReset:
        password_reset = uow.users.get_password_reset_by_id(password_reset_id)
        if not password_reset:
            raise NotFoundError("PasswordReset not found", target="password_reset_id")
        return password_reset

    def list_user_filter(
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
            rows = uow.users.list_user_filter(
                status=status,
                role=role,
                limit=limit,
                offset=offset,
            )

            user_infos = []
            for user in rows:
                user_info = UserDTO.UserAdminInfo(
                    id=user.id,
                    email=(
                        self._secrets.decrypt(
                            ciphertext=user.email_ciphertext,
                            nonce=user.email_nonce,
                        ).decode("utf-8")
                        if user.email_ciphertext and user.email_nonce
                        else None
                    ),
                    nickname=user.nickname,
                    role=user.role,
                    status=user.status,
                    created_at=user.created_at,
                    last_login_at=user.last_login_at,
                )

                user_infos.append(user_info)
            return user_infos

    def get_user_public_info(self, *, user_id: int) -> UserDTO.UserPublicInfo:
        with self._uow_factory() as uow:
            user = uow.users.get_with_provider_by_user_id(user_id=user_id)

            if not user:
                raise NotFoundError("User not found", target="User")

            if user.email_ciphertext is None or user.email_nonce is None:
                raise ValidationAppError("user email is not set", target="user.email")

            user.email=(
                self._secrets.decrypt(
                    ciphertext=user.email_ciphertext,
                    nonce=user.email_nonce,
                ).decode("utf-8")
                if user.email_ciphertext and user.email_nonce
                else None
            )

            return user

    def get_user_email_info(self, *, user_id: int) -> UserDTO.UserEmailInfo:
        with self._uow_factory() as uow:
            user = self._ensure_user(uow, user_id)

            if user.email_ciphertext is None or user.email_nonce is None:
                raise ValidationAppError("user email is not set", target="user.email")

            user_info = UserDTO.UserEmailInfo(
                id=user.id,
                nickname=user.nickname,
                email_ciphertext=user.email_ciphertext,
                email_fingerprint=user.email_fingerprint,
                email_nonce=user.email_nonce,
                email_key_version=user.email_key_version,
                email_verified_at=user.email_verified_at,
            )

            return user_info

    def get_user_admin_info(self, *, user_id: int) -> UserDTO.UserAdminInfo:
        with self._uow_factory() as uow:
            user = self._ensure_user(uow, user_id)

            user_info = UserDTO.UserAdminInfo(
                id=user.id,
                email=(
                    self._secrets.decrypt(
                        ciphertext=user.email_ciphertext,
                        nonce=user.email_nonce,
                    ).decode("utf-8")
                    if user.email_ciphertext and user.email_nonce
                    else None
                ),
                nickname=user.nickname,
                role=user.role,
                status=user.status,
                created_at=user.created_at,
                last_login_at=user.last_login_at,
            )

            return user_info

    def get_password_reset_by_id(
        self, *, password_reset_id: int
    ) -> UserDTO.PasswordReset:
        with self._uow_factory() as uow:
            password_reset = self._ensure_password_reset(uow, password_reset_id)

            return password_reset

    def get_email_verification_by_id(
        self, *, email_verification_id: int
    ) -> UserDTO.EmailVerification:
        with self._uow_factory() as uow:
            email_verification = self._ensure_email_verification(
                uow, email_verification_id
            )
            return email_verification

    def get_email_verification_by_token_hash(
        self, *, token_hash: bytes
    ) -> UserDTO.EmailVerification:
        with self._uow_factory() as uow:
            email_verification = uow.users.get_email_verification_by_token_hash(
                token_hash
            )
            if not email_verification:
                raise NotFoundError("EmailVerification not found", target="token_hash")

            return email_verification

    def change_user_settings(self, user_id: int, is_marketing: bool | None = None, is_quiet_hours: bool | None = None): 
        if(is_marketing is None and is_quiet_hours is None):
            raise ValidationAppError("Invalid user setting", target="user")
            
        now = utcnow()
        with self._uow_factory() as uow:
            user = uow.users.get_by_user_id(user_id)
            if not user:
                raise AuthError("Invalid credentials", target="user")

            uow.users.update_user_settings(user_id, is_marketing, is_quiet_hours)
            uow.commit()

            return {"ok": True}

    def change_password_reset_sent(self, *, password_reset_id: int) -> None:
        now = utcnow()

        with self._uow_factory() as uow:
            uow.users.update_password_reset_by_filter(
                id=password_reset_id,
                expires_after=now,
                sent_at=now,
                sent_is_null=True,
                consumed_is_null=True,  # 멱등성 보장 (이미 보낸 건 다시 안 찍음)
            )
            uow.commit()

    def change_email_verification_sent(self, *, email_verification_id: int) -> None:
        now = utcnow()
        with self._uow_factory() as uow:
            uow.users.update_email_verification_by_filter(
                filters=EmailDTO.EmailVerificationFilter(
                    id=email_verification_id,
                    statuses=(EmailVerificationStatus.PENDING,),
                    expires_after=now,  # 만료 안 된 것만
                ),
                updates=EmailDTO.EmailVerificationUpdate(
                    status=EmailVerificationStatus.SENT,
                    sent_at=now,
                ),
            )
            uow.commit()
