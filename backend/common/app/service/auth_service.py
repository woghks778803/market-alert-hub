from typing import Callable, Dict, Any
from datetime import datetime, timedelta, timezone

from app.domain.uow import UnitOfWork
from app.infra.db.model import UserModel, OutboxModel, EmailVerificationModel
from app.domain import AuthDTO, EmailDTO, ValidationAppError, AuthError, PermissionError, CryptoPort
from app.core.constants import UserRole, UserStatus, OutboxStatus, EmailVerificationStatus
from app.core import dto as CoreDTO
from app.core.util.datetime import utcnow, ensure_utc
from app.core.util.serialization import to_canonical_json


class AuthService:
    def __init__(
        self,
        *,
        trace_id: str | None,
        redis_client: Callable[[], Any],
        uow_factory: Callable[[], UnitOfWork],
        password: CryptoPort.PasswordHasher,
        hmac: CryptoPort.TokenHasher,
        jwt: CryptoPort.TokenSigner,
        secrets: CryptoPort.SecretCrypto,
        config: CoreDTO.ConfigBag,
    ) -> None:
        self._trace_id = trace_id
        self._redis_client = redis_client
        self._uow_factory = uow_factory
        self._password = password
        self._hmac = hmac
        self._jwt = jwt
        self._secrets = secrets
        self._config = config

    # 회원가입
    def register(
        self,
        *,
        email: str,
        nickname: str,
        password: str,
    ):
        now = utcnow()
        expires_at = now + timedelta(minutes=self._config.access_token_minutes)

        with self._uow_factory() as uow:
            email_fingerprint = self._hmac.fp_hash(email)
            email_secrets = self._secrets.encrypt(email.encode("utf-8"))

            if uow.users.get_user_by_email_fingerprint(email_fingerprint):
                raise ValidationAppError("email_fingerprint already exists", target="email_fingerprint")

            user = UserModel(
                email_fingerprint=email_fingerprint,
                email_ciphertext=email_secrets["ciphertext"],
                email_nonce=email_secrets["nonce"],
                email_key_version=self._config.crypto_data_kid,
                email_verified_at=None,
                nickname=nickname,
                password_hash=self._password.hash_password(password),
                # role/status 기본값은 모델 default/enum 디폴트 사용
            )

            uow.users.add_user(user)

            email_token = self._jwt.create_access_token(
                subject=str(user.id), minutes=self._config.access_token_minutes
            )

            email_verification = EmailVerificationModel(
                user_id=user.id,
                email_fingerprint=email_fingerprint,
                email_ciphertext=email_secrets["ciphertext"],
                email_nonce=email_secrets["nonce"],
                email_key_version=self._config.crypto_data_kid,
                token_hash=self._hmac.token_hash(email_token),
                status=EmailVerificationStatus.PENDING,
                expires_at=expires_at,
            )

            uow.users.add_email_verification(email_verification)

            outbox_fingerprint_dict = {"event_type": "EMAIL_AUTH_CODE", "aggregate_type": "user", "aggregate_id": user.id, "email_verification_id": email_verification.id}
            outbox_fingerprint = to_canonical_json(outbox_fingerprint_dict)
            if outbox_fingerprint is not None: outbox_fingerprint= self._hmac.fp_hash(outbox_fingerprint)

            uow.outboxs.add_outbox(
                OutboxModel(
                    trace_id=self._trace_id,
                    event_type="EMAIL_AUTH_CODE",
                    aggregate_type="user",
                    aggregate_id=user.id,
                    outbox_fingerprint=outbox_fingerprint,
                    payload={"user_id": user.id, "email_verification_id": email_verification.id, "verify_token": email_token},
                    status=OutboxStatus.PENDING,
                    attempts=0,
                )
            )

            uow.commit()

            return {"ok": True}

    # 로그인
    def login(
        self,
        *,
        email: str,
        password: str,
        ip: str | None = None,
        ua: str | None = None,
        admin_chk: bool = False,
    ) -> AuthDTO.AuthToken:
        now = utcnow()
        expires_at = now + timedelta(minutes=self._config.access_token_minutes)

        with self._uow_factory() as uow:
            email_fingerprint = self._hmac.fp_hash(email)
            user = uow.users.get_user_by_email_fingerprint(email_fingerprint)
            if not user or not self._password.verify_password(
                password, user.password_hash
            ):
                raise AuthError("Invalid credentials")

            if admin_chk == True and user.role != UserRole.ADMIN:
                raise PermissionError("Admin role required", target="role")

            if user.status != UserStatus.ACTIVE:
                raise PermissionError("User not active status", target="status")
            
            if user.email_verified_at is None:
                raise PermissionError("Email not verified", target="email_verified_at")

            token = self._jwt.create_access_token(
                subject=str(user.id), minutes=self._config.access_token_minutes
            )

            uow.sessions.add_session(
                user_id=user.id,
                token_hash=self._hmac.token_hash(token),
                expires_at=expires_at,
                ip_addr=ip,
                user_agent=ua,
            )

            user.last_login_at = now
            uow.commit()

            return AuthDTO.AuthToken(access_token=token)

    # 로그아웃 (세션 무효화)
    def logout(self, *, token: str) -> Dict[str, Any]:
        with self._uow_factory() as uow:
            uow.sessions.update_session(self._hmac.token_hash(token))
            uow.commit()
            return {"ok": True}

    def resend_email_verification(
        self,
        *,
        email: str,
        password: str,
        ip: str | None = None,
        ua: str | None = None,
    ) -> Dict[str, Any]:
        now = utcnow()
        expires_at = now + timedelta(minutes=self._config.access_token_minutes)

        with self._uow_factory() as uow:
            email_fingerprint = self._hmac.fp_hash(email)
            user = uow.users.get_user_by_email_fingerprint(email_fingerprint)
            if not user or not self._password.verify_password(
                password, user.password_hash
            ):
                raise AuthError("Invalid credentials")

            if user.email_verified_at is not None:
                raise ValidationAppError("Email already verified", target="email_verified_at")
            
            # ✅ 쿨다운 (연타 방지)
            cooldown_sec = self._config.email_verify_resend_cooldown_sec
            key = f"cooldown:email_verify_resend:{user.id}"
            ok = self._redis_client().set(key, b"1", nx=True, ex_sec=cooldown_sec)
            if not ok:
                remain = self._redis_client().ttl(key)  # -2/-1 처리만 조심
                remain = remain if remain > 0 else 0 # 가드
                raise ValidationAppError(
                    "Too many requests. Please try again later.",
                    target="resend",
                    meta={"cooldown_remaining_sec": max(remain, 0)},
                )

            # 이전 pending, send 인증 메일 무효화
            affected = uow.users.update_email_verification_by_filter(
                filters=EmailDTO.EmailVerificationFilter(
                    user_id=user.id,
                    statuses=(EmailVerificationStatus.PENDING, EmailVerificationStatus.SENT),
                    expires_after=now,  # expires_at > now 인 것만
                ),
                updates=EmailDTO.EmailVerificationUpdate(
                    status=EmailVerificationStatus.CANCELLED,
                    expires_at=now,
                ),
            )

            email_token = self._jwt.create_access_token(
                subject=str(user.id), minutes=self._config.access_token_minutes
            )

            email_verification = EmailVerificationModel(
                user_id=user.id,
                email_fingerprint=user.email_fingerprint,
                email_ciphertext=user.email_ciphertext,
                email_nonce=user.email_nonce,
                email_key_version=user.email_key_version,
                token_hash=self._hmac.token_hash(email_token),
                status=EmailVerificationStatus.PENDING,
                expires_at=expires_at,
            )

            uow.users.add_email_verification(email_verification)

            outbox_fingerprint_dict = {"event_type": "EMAIL_AUTH_CODE", "aggregate_type": "user", "aggregate_id": user.id, "email_verification_id": email_verification.id}
            outbox_fingerprint = to_canonical_json(outbox_fingerprint_dict)
            if outbox_fingerprint is not None: outbox_fingerprint= self._hmac.fp_hash(outbox_fingerprint)

            uow.outboxs.add_outbox(
                OutboxModel(
                    trace_id=self._trace_id,
                    event_type="EMAIL_AUTH_CODE",
                    aggregate_type="user",
                    aggregate_id=user.id,
                    outbox_fingerprint=outbox_fingerprint,
                    payload={"user_id": user.id, "email_verification_id": email_verification.id, "verify_token": email_token},
                    status=OutboxStatus.PENDING,
                    attempts=0,
                )
            )

            uow.commit()

            return {"ok": True}

    def verify_email(
        self, 
        *, 
        token: str,
        ip: str | None = None,
        ua: str | None = None,
    ) -> None:
        now = utcnow()

        token_hash = self._hmac.token_hash(token)

        with self._uow_factory() as uow:
            
            email_verification = uow.users.get_email_verification_by_token_hash(token_hash)

            if not email_verification:
                raise ValidationAppError("Token not found", target="token")

            if email_verification.status != EmailVerificationStatus.SENT:
                raise ValidationAppError("Invalid status", target="status")

            expires_at = ensure_utc(email_verification.expires_at)
            if expires_at <= now:
                raise ValidationAppError("Token expired", target="token")

            user = uow.users.get_by_user_id(email_verification.user_id)
            if not user:
                raise ValidationAppError("User not found", target="user_id")

            user.email_verified_at = now
            email_verification.status = EmailVerificationStatus.CONSUMED
            email_verification.consumed_at = now


            uow.commit()
    
    def change_email(
        self, *, user_id: int, session_token: str, current_password: str, new_email: str
    ):
        now = utcnow()
        expires_at = now + timedelta(minutes=self._config.access_token_minutes)

        with self._uow_factory() as uow:
            user = uow.users.get_by_user_id(user_id)
            if not user:
                raise ValidationAppError("User not found", target="user_id")
            
            if not self._password.verify_password(
                current_password, user.password_hash
            ):
                raise ValidationAppError("Current password is incorrect", target="current_password")
            
            new_email_fingerprint = self._hmac.fp_hash(new_email)
            new_email_secrets = self._secrets.encrypt(new_email.encode("utf-8"))
            if uow.users.get_user_by_email_fingerprint(new_email_fingerprint):
                raise ValidationAppError("email_fingerprint already exists", target="new_email")

            
            email_token = self._jwt.create_access_token(
                subject=str(user.id), minutes=self._config.access_token_minutes
            )

            email_verification = EmailVerificationModel(
                user_id=user.id,
                email_fingerprint=new_email_fingerprint,
                email_ciphertext=new_email_secrets["ciphertext"],
                email_nonce=new_email_secrets["nonce"],
                email_key_version=self._config.crypto_data_kid,
                token_hash=self._hmac.token_hash(email_token),
                status=EmailVerificationStatus.PENDING,
                expires_at=expires_at,
            )

            uow.users.add_email_verification(email_verification)
            
            outbox_fingerprint_dict = {"event_type": "EMAIL_AUTH_CODE", "aggregate_type": "user", "aggregate_id": user.id, "email_verification_id": email_verification.id}
            outbox_fingerprint = to_canonical_json(outbox_fingerprint_dict)
            if outbox_fingerprint is not None: outbox_fingerprint= self._hmac.fp_hash(outbox_fingerprint)

            uow.outboxs.add_outbox(
                OutboxModel(
                    trace_id=self._trace_id,
                    event_type="EMAIL_AUTH_CODE",
                    aggregate_type="user",
                    aggregate_id=user.id,
                    outbox_fingerprint=outbox_fingerprint,
                    payload={"user_id": user.id, "email_verification_id": email_verification.id, "verify_token": email_token},
                    status=OutboxStatus.PENDING,
                    attempts=0,
                )
            )

            user.email_fingerprint = new_email_fingerprint
            user.email_ciphertext = new_email_secrets["ciphertext"] 
            user.email_nonce = new_email_secrets["nonce"]
            user.email_key_version = self._config.crypto_data_kid
            user.email_verified_at = None
            uow.sessions.update_session(self._hmac.token_hash(session_token))
            uow.commit()
            return {"ok": True}

    def get_current_user(self, user_id: int, token: str):
        now = utcnow()
        with self._uow_factory() as uow:

            user = uow.users.get_by_user_id(user_id)
            if not user:
                raise AuthError("Invalid credentials", target="token")

            # 세션 유효성(선택이지만 권장)
            s = uow.sessions.get_session_by_hash(self._hmac.token_hash(token))
            if s is None:
                raise AuthError("Invalid credentials", target="token")

            expires_at = ensure_utc(s.expires_at)
            revoked_at = s.revoked_at
            if revoked_at is not None and revoked_at.tzinfo is None:
                revoked_at = revoked_at.replace(tzinfo=timezone.utc)

            if not s or revoked_at or expires_at <= now:
                raise AuthError("Missing or invalid token", target="token")

            return AuthDTO.AuthUser(access_token=token, id=user.id, role=user.role)
