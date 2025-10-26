import json
from typing import Callable, Dict, Any
from datetime import datetime, timedelta, timezone

from app.domain.uow import UnitOfWork
from app.infra.db.model import UserModel, OutboxModel
from app.domain import AuthDTO, ValidationAppError, AuthError, PermissionError
from app.core.constants import UserRole, UserStatus, OutboxStatus
from app.core.datetime_utils import utcnow
from app.domain import CryptoPort


class AuthService:
    def __init__(
        self,
        *,
        uow_factory: Callable[[], UnitOfWork],
        password: CryptoPort.PasswordHasher,
        jwt: CryptoPort.TokenSigner,
        jwt_secret: str,
        token_minutes: int,
    ) -> None:
        self._uow_factory = uow_factory
        self._password = password
        self._jwt = jwt
        self._secret = jwt_secret
        self._ttl = token_minutes

    # 회원가입
    def signup(
        self,
        *,
        email: str,
        nickname: str,
        password: str,
        ip: str | None = None,
        ua: str | None = None,
    ):
        now = utcnow()
        expires_at = now + timedelta(minutes=self._ttl)

        with self._uow_factory() as uow:

            if uow.users.get_user_by_email(email):
                raise ValidationAppError("email already exists", target="email")

            user = UserModel(
                email=email,
                nickname=nickname,
                password_hash=self._password.hash_password(password),
                # role/status 기본값은 모델 default/enum 디폴트 사용
            )

            uow.users.add_user(user)

            token = self._jwt.create_access_token(
                subject=str(user.id), minutes=self._ttl
            )
            uow.sessions.create_session(
                user_id=user.id,
                token_hash=self._jwt.token_hash(token),
                expires_at=expires_at,
                ip_addr=ip,
                user_agent=ua,
            )

            uow.outboxs.add_outbox(
                OutboxModel(
                    event_type="EMAIL_AUTH_CODE",
                    aggregate_type="user",
                    aggregate_id=user.id,
                    status=OutboxStatus.PENDING,
                    attempts=0,
                )
            )

            # trace_id 생성

            #

            # uow.outboxs.add_outbox(OutboxModel(
            #     event_type="EMAIL_SIGNUP",
            #     aggregate_type="user",
            #     aggregate_id=user.id,
            #     status=OutboxStatus.PENDING,
            #     attempts=0,
            # ))

            uow.commit()

            return AuthDTO.AuthToken(access_token=token)

    # 로그인
    def signin(
        self,
        *,
        email: str,
        password: str,
        ip: str | None = None,
        ua: str | None = None,
        admin_chk: bool = False,
    ) -> AuthDTO.AuthToken:
        now = utcnow()
        expires_at = now + timedelta(minutes=self._ttl)

        with self._uow_factory() as uow:
            user = uow.users.get_user_by_email(email)
            if not user or not self._password.verify_password(
                password, user.password_hash
            ):
                raise AuthError("invalid_credentials")

            if admin_chk == True and user.role != UserRole.ADMIN:
                raise PermissionError("Admin role required", target="role")

            if user.status != UserStatus.ACTIVE:
                raise PermissionError("User not active status", target="status")

            token = self._jwt.create_access_token(
                subject=str(user.id), minutes=self._ttl
            )

            uow.sessions.create_session(
                user_id=user.id,
                token_hash=self._jwt.token_hash(token),
                expires_at=expires_at,
                ip_addr=ip,
                user_agent=ua,
            )

            user.last_login_at = now
            uow.commit()

            return AuthDTO.AuthToken(access_token=token)

    # 로그아웃 (세션 무효화)
    def logout(self, *, token_hash: str) -> Dict[str, Any]:
        with self._uow_factory() as uow:
            uow.sessions.update_session(token_hash)
            uow.commit()
            return {"ok": True}

    def get_current_user(self, user_id: int, token: str):
        now = utcnow()

        with self._uow_factory() as uow:

            user = uow.users.get_by_user_id(user_id)
            if not user:
                raise AuthError("Invalid credentials", target="token")

            # 세션 유효성(선택이지만 권장)
            s = uow.sessions.get_session_by_hash(self._jwt.token_hash(token))
            if s is None:
                raise AuthError("Invalid credentials", target="token")

            expires_at = s.expires_at
            revoked_at = s.revoked_at

            if expires_at is not None and expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)
            if revoked_at is not None and revoked_at.tzinfo is None:
                revoked_at = revoked_at.replace(tzinfo=timezone.utc)

            if not s or revoked_at or expires_at <= now:
                raise AuthError("Missing or invalid token", target="token")

            return AuthDTO.AuthUser(id=user.id, email=user.email, role=user.role)
