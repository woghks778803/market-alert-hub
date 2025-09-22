# app/service/auth_service.py
from __future__ import annotations
from typing import Callable, Dict, Any, Optional
from datetime import datetime, timedelta, timezone

from app.service.uow import UnitOfWork
from app.infra.db.model.user import User
from app.domain.errors import ValidationAppError, AuthError
from app.core.auth import hash_password, verify_password, create_access_token, token_hash


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
        ip: Optional[str] = None,
        ua: Optional[str] = None,
    ) -> Dict[str, Any]:
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(minutes=self._ttl)

        with self._uow_factory() as uow:
            # 레포 구현 직접 호출/생성 X → uow.users 사용
            if uow.users.get_by_email(email):
                raise ValidationAppError("email already exists")
            
            user = User(
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

            return {
                "id": user.id,
                "email": user.email,
                "nickname": user.nickname,
                "created_at": user.created_at
            }

    # 로그인
    def login(
        self,
        *,
        email: str,
        password: str,
        ip: Optional[str] = None,
        ua: Optional[str] = None,
    ) -> Dict[str, Any]:
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(minutes=self._ttl)

        with self._uow_factory() as uow:
            user = uow.users.get_by_email(email)
            if not user or not verify_password(password, user.password_hash):
                raise AuthError("invalid_credentials")

            user.last_login_at = now  # flush는 레포 내부/세션 정책대로
            token = create_access_token(sub=str(user.id), minutes=self._ttl)

            uow.sessions.create(
                user_id=user.id,
                token_hash=token_hash(token),
                expires_at=expires_at,
                ip_addr=ip,
                user_agent=ua,
            )

            uow.commit()

            return {
                "user_id": user.id,
                "access_token": token,
                "token_type": "bearer",
                "expires_at": int(expires_at.timestamp()),
            }

    # 로그아웃 (세션 무효화)
    def logout(self, *, token_hash: str) -> Dict[str, Any]:
        with self._uow_factory() as uow:
            uow.sessions.revoke(token_hash)
            uow.commit()
            return {"ok": True}

    # 내 정보 (필요하면)
    def me(self, *, user_id: int) -> Dict[str, Any]:
        with self._uow_factory() as uow:
            user = uow.users.get_by_id(user_id)
            if not user:
                raise AuthError("user_not_found")
            return {
                "id": user.id,
                "email": user.email,
                "role": str(user.role),
                "status": str(user.status),
                "last_login_at": user.last_login_at.isoformat() if user.last_login_at else None,
            }
