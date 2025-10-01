# app/service/auth_service.py
from __future__ import annotations
from typing import Callable, Dict, Any, Optional
from datetime import datetime, timedelta, timezone

from app.service.uow import UnitOfWork
from app.infra.db.model import UserModel
from app.domain import AuthDTO, ValidationAppError, AuthError, PermissionError
from app.core.auth import hash_password, verify_password, create_access_token, token_hash
from app.core.constants import UserRole, UserStatus


class AuthService:
    def __init__(
        self,
        *,
        uow_factory: Callable[[], UnitOfWork],
        jwt_secret: str,
        token_minutes: int,
    ) -> None:
        self._uow_factory = uow_factory
        self._secret = jwt_secret
        self._ttl = token_minutes

    # 회원가입
    def register(
        self,
        *,
        email: str,
        nickname: str,
        password: str,
        ip: str | None = None,
        ua: str | None = None,
    ) -> Dict[str, Any]:
        
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(minutes=self._ttl)
        
        with self._uow_factory() as uow:

            if uow.users.get_by_email(email):
                raise ValidationAppError("email already exists", target="email")

            user = UserModel(
                email=email,
                nickname=nickname,
                password_hash=hash_password(password),
                # role/status 기본값은 모델 default/enum 디폴트 사용
                created_at=now,
            )

            uow.users.add(user)

            token = create_access_token(sub=str(user.id), minutes=self._ttl)
            uow.sessions.create(
                user_id=user.id,
                token_hash=token_hash(token),
                expires_at=expires_at,
                ip_addr=ip,
                user_agent=ua,
            )

            uow.commit()

            return AuthDTO.UserToken(user_id=user.id, access_token=token)

    # 로그인
    def login(
        self,
        *,
        email: str,
        password: str,
        ip: str | None = None,
        ua: str | None = None,
        admin_chk: bool = False,
    ) -> AuthDTO.UserToken:
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(minutes=self._ttl)
        
        with self._uow_factory() as uow:
            user = uow.users.get_by_email(email)
            if not user or not verify_password(password, user.password_hash):
                raise AuthError("invalid_credentials")

            if admin_chk == True and user.role != UserRole.ADMIN:
                raise PermissionError("Admin role required", target="role")
            
            if user.status != UserStatus.ACTIVE:
                raise PermissionError("User not active status", target="status")
            
            token = create_access_token(sub=str(user.id), minutes=self._ttl)

            uow.sessions.create(
                user_id=user.id,
                token_hash=token_hash(token),
                expires_at=expires_at,
                ip_addr=ip,
                user_agent=ua,
            )

            user.last_login_at = now
            uow.commit()

            return AuthDTO.UserToken(user_id=user.id, access_token=token)

    # 로그아웃 (세션 무효화)
    def logout(self, *, token_hash: str) -> Dict[str, Any]:
        with self._uow_factory() as uow:
            uow.sessions.revoke(token_hash)
            uow.commit()
            return {"ok": True}