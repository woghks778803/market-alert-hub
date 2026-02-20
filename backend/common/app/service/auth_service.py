from encodings.punycode import T
from typing import Callable, Dict, Any
from datetime import datetime, timedelta, timezone

from app.core.constants import (
    UserRole,
    UserStatus,
    OutboxStatus,
    EmailVerificationStatus,
    OutboxEventType,
)
from app.core import dto as CoreDTO
from app.core.util.trace import get_trace_id
from app.core.util.datetime import utcnow, ensure_utc
from app.core.util.serialization import to_canonical_json
from app.domain.shared.uow import UnitOfWork
from app.domain.shared.errors import (
    ValidationAppError,
    PermissionError,
    ConflictError,
    AuthError,
)
from app.domain import (
    OutboxDTO,
    UserDTO,
    AuthDTO,
    EmailDTO,
    CryptoPort,
)


class AuthService:
    def __init__(
        self,
        *,
        redis_client: Callable[[], Any],
        uow_factory: Callable[[], UnitOfWork],
        password: CryptoPort.PasswordHasher,
        hmac: CryptoPort.TokenHasher,
        jwt: CryptoPort.TokenSigner,
        secrets: CryptoPort.SecretCrypto,
        config: CoreDTO.ServiceConfigBag,
    ) -> None:
        self._redis_client = redis_client
        self._uow_factory = uow_factory
        self._password = password
        self._hmac = hmac
        self._jwt = jwt
        self._secrets = secrets
        self._config = config

    def _enqueue_email_auth_code_outbox_in_tx(
        self,
        *,
        uow: UnitOfWork,  # 너 프로젝트 UoW 타입
        trace_id: str,
        user_id: int,
        email_fingerprint: bytes,
        email_ciphertext: bytes,
        email_nonce: bytes,
        email_key_version: int,
        expires_at: datetime,
        cancel_pending: bool = False,
        now: datetime | None = None,
    ) -> AuthDTO.EmailVerificationEnqueueResult:
        """
        트랜잭션 내부 전용 공통 함수.
        """
        now = now or datetime.utcnow()

        # 0) (선택) 기존 pending/sent 취소
        if cancel_pending:
            uow.users.update_email_verification_by_filter(
                filters=EmailDTO.EmailVerificationFilter(
                    user_id=user_id,
                    statuses=(
                        EmailVerificationStatus.PENDING,
                        EmailVerificationStatus.SENT,
                    ),
                    expires_after=now,  # "만료 안 된 것만" 취소하려면 now 기준
                ),
                updates=EmailDTO.EmailVerificationUpdate(
                    status=EmailVerificationStatus.CANCELLED,
                    expires_at=now,
                ),
            )

        # 1) verify token 생성 (plain token은 outbox payload로만)
        email_token = self._jwt.create_access_token(
            subject=str(user_id),
            minutes=self._config.access_token_minutes,
        )

        # 2) email_verification row 생성 (DB에는 해시만)
        email_verification = uow.users.add_email_verification(
            UserDTO.EmailVerificationCreate(
                user_id=user_id,
                email_fingerprint=email_fingerprint,
                email_ciphertext=email_ciphertext,
                email_nonce=email_nonce,
                email_key_version=email_key_version,
                token_hash=self._hmac.token_hash(email_token),
                expires_at=expires_at,
            )
        )

        # 3) outbox fingerprint (중복 방지)
        fp_dict: dict[str, Any] = {
            "event_type": OutboxEventType.EMAIL_AUTH_CODE,
            "aggregate_type": "user",
            "aggregate_id": user_id,
            "email_verification_id": email_verification.id,
        }

        outbox_fingerprint = to_canonical_json(fp_dict)
        outbox_fingerprint = (
            self._hmac.fp_hash(outbox_fingerprint)
            if outbox_fingerprint is not None
            else None
        )

        # 4) outbox enqueue
        uow.outboxs.add_outbox(
            OutboxDTO.OutboxCreate(
                trace_id=trace_id,
                event_type=OutboxEventType.EMAIL_AUTH_CODE,
                aggregate_type="user",
                aggregate_id=user_id,
                outbox_fingerprint=outbox_fingerprint,
                payload={
                    "user_id": user_id,
                    "email_verification_id": email_verification.id,
                    "verify_token": email_token,
                },
                status=OutboxStatus.PENDING,
                attempts=0,
            ),
            True,
        )

        return AuthDTO.EmailVerificationEnqueueResult(
            email_verification_id=email_verification.id,
            verify_token=email_token,
            expires_at=expires_at,
            outbox_fingerprint=outbox_fingerprint,
        )

    # 회원가입
    def register(
        self,
        *,
        email: str,
        nickname: str,
        password: str,
        agree_service: bool,
        agree_privacy: bool,
        agree_marketing: bool,
        ip: str | None = None,
        ua: str | None = None,
    ):
        now = utcnow()
        trace_id = get_trace_id()

        expires_at = now + timedelta(minutes=self._config.access_token_minutes)

        with self._uow_factory() as uow:
            email_fingerprint = self._hmac.fp_hash(email)
            email_secrets = self._secrets.encrypt(email.encode("utf-8"))

            if uow.users.get_user_by_email_fingerprint(email_fingerprint):
                raise ConflictError("email_fingerprint already exists", target="email")

            user = uow.users.add_user(
                UserDTO.UserCreate(
                    email_fingerprint=email_fingerprint,
                    email_ciphertext=email_secrets["ciphertext"],
                    email_nonce=email_secrets["nonce"],
                    email_key_version=self._config.crypto_data_kid,
                    nickname=nickname,
                    password_hash=self._password.hash_password(password),
                    is_service=agree_service,
                    is_privacy=agree_privacy,
                    is_marketing=agree_marketing,
                    # role/status 기본값은 모델 default/enum 디폴트 사용
                )
            )

            self._enqueue_email_auth_code_outbox_in_tx(
                uow=uow,
                trace_id=trace_id,
                user_id=user.id,
                email_fingerprint=email_fingerprint,
                email_ciphertext=email_secrets["ciphertext"],
                email_nonce=email_secrets["nonce"],
                email_key_version=self._config.crypto_data_kid,
                expires_at=expires_at,
                cancel_pending=False,
                now=now,
            )
            # email_token = self._jwt.create_access_token(
            #     subject=str(user.id), minutes=self._config.access_token_minutes
            # )

            # email_verification = uow.users.add_email_verification(
            #     UserDTO.EmailVerificationCreate(
            #         user_id=user.id,
            #         email_fingerprint=email_fingerprint,
            #         email_ciphertext=email_secrets["ciphertext"],
            #         email_nonce=email_secrets["nonce"],
            #         email_key_version=self._config.crypto_data_kid,
            #         token_hash=self._hmac.token_hash(email_token),
            #         expires_at=expires_at,
            #     )
            # )

            # outbox_fingerprint_dict = {
            #     "event_type": OutboxEventType.EMAIL_AUTH_CODE,
            #     "aggregate_type": "user",
            #     "aggregate_id": user.id,
            #     "email_verification_id": email_verification.id,
            # }
            # outbox_fingerprint = to_canonical_json(outbox_fingerprint_dict)
            # if outbox_fingerprint is not None:
            #     outbox_fingerprint = self._hmac.fp_hash(outbox_fingerprint)

            # uow.outboxs.add_outbox(
            #     OutboxDTO.OutboxCreate(
            #         trace_id=trace_id,
            #         event_type=OutboxEventType.EMAIL_AUTH_CODE,
            #         aggregate_type="user",
            #         aggregate_id=user.id,
            #         outbox_fingerprint=outbox_fingerprint,
            #         payload={
            #             "user_id": user.id,
            #             "email_verification_id": email_verification.id,
            #             "verify_token": email_token,
            #         },
            #         status=OutboxStatus.PENDING,
            #         attempts=0,
            #     ),
            #     True,
            # )

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
                cooldown_sec = self._config.email_verify_resend_cooldown_sec
                key = f"cooldown:email_verify_resend:{user.id}"
                ok = self._redis_client().set(key, b"1", nx=True, ex=cooldown_sec)
                if ok:
                    self._enqueue_email_auth_code_outbox_in_tx(
                        uow=uow,
                        trace_id=get_trace_id(),
                        user_id=user.id,
                        email_fingerprint=user.email_fingerprint,
                        email_ciphertext=user.email_ciphertext,
                        email_nonce=user.email_nonce,
                        email_key_version=user.email_key_version,
                        expires_at=expires_at,
                        cancel_pending=True,
                        now=now,
                    )

            token = self._jwt.create_access_token(
                subject=str(user.id),
                minutes=self._config.access_token_minutes,
                claims={"ev": bool(user.email_verified_at)},
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
        user_id: int,
    ) -> Dict[str, Any]:
        now = utcnow()
        trace_id = get_trace_id()
        expires_at = now + timedelta(minutes=self._config.access_token_minutes)

        with self._uow_factory() as uow:
            user = uow.users.get_by_user_id(user_id)
            if not user:
                raise AuthError("Invalid credentials")

            if user.email_verified_at is not None:
                raise ConflictError("Email already verified", target="email")

            if user.email_fingerprint is None:
                raise ValidationAppError(
                    message="User email_fingerprint is missing",
                    target="users.email_fingerprint",
                    meta={"user_id": user.id},
                )
            if user.email_ciphertext is None:
                raise ValidationAppError(
                    message="User email_ciphertext is missing",
                    target="users.email_ciphertext",
                    meta={"user_id": user.id},
                )
            if user.email_nonce is None:
                raise ValidationAppError(
                    message="User email_nonce is missing",
                    target="users.email_nonce",
                    meta={"user_id": user.id},
                )
            if user.email_key_version is None:
                raise ValidationAppError(
                    message="User email_key_version is missing",
                    target="users.email_key_version",
                    meta={"user_id": user.id},
                )

            email_fingerprint = user.email_fingerprint
            email_ciphertext = user.email_ciphertext
            email_nonce = user.email_nonce
            email_key_version = user.email_key_version

            #  쿨다운 (연타 방지)
            cooldown_sec = self._config.email_verify_resend_cooldown_sec
            key = f"cooldown:email_verify_resend:{user.id}"
            ok = self._redis_client().set(key, b"1", nx=True, ex=cooldown_sec)
            if not ok:
                remain = self._redis_client().ttl(key)  # -2/-1 처리만 조심
                remain = remain if remain > 0 else 0  # 가드
                raise ValidationAppError(
                    "Too many requests. Please try again later.",
                    target="resend",
                    meta={"cooldown_remaining_sec": max(remain, 0)},
                )

            self._enqueue_email_auth_code_outbox_in_tx(
                uow=uow,
                trace_id=trace_id,
                user_id=user.id,
                email_fingerprint=email_fingerprint,
                email_ciphertext=email_ciphertext,
                email_nonce=email_nonce,
                email_key_version=email_key_version,
                expires_at=expires_at,
                cancel_pending=True,
                now=now,
            )

            # 이전 pending, send 인증 메일 무효화
            # affected = uow.users.update_email_verification_by_filter(
            #     filters=EmailDTO.EmailVerificationFilter(
            #         user_id=user.id,
            #         statuses=(
            #             EmailVerificationStatus.PENDING,
            #             EmailVerificationStatus.SENT,
            #         ),
            #         expires_after=now,  # expires_at > now 인 것만
            #     ),
            #     updates=EmailDTO.EmailVerificationUpdate(
            #         status=EmailVerificationStatus.CANCELLED,
            #         expires_at=now,
            #     ),
            # )

            # email_token = self._jwt.create_access_token(
            #     subject=str(user.id), minutes=self._config.access_token_minutes
            # )

            # email_verification = uow.users.add_email_verification(
            #     UserDTO.EmailVerificationCreate(
            #         user_id=user.id,
            #         email_fingerprint=email_fingerprint,
            #         email_ciphertext=email_ciphertext,
            #         email_nonce=email_nonce,
            #         email_key_version=email_key_version,
            #         token_hash=self._hmac.token_hash(email_token),
            #         expires_at=expires_at,
            #     )
            # )

            # outbox_fingerprint_dict = {
            #     "event_type": OutboxEventType.EMAIL_AUTH_CODE,
            #     "aggregate_type": "user",
            #     "aggregate_id": user.id,
            #     "email_verification_id": email_verification.id,
            # }
            # outbox_fingerprint = to_canonical_json(outbox_fingerprint_dict)
            # if outbox_fingerprint is not None:
            #     outbox_fingerprint = self._hmac.fp_hash(outbox_fingerprint)

            # uow.outboxs.add_outbox(
            #     OutboxDTO.OutboxCreate(
            #         trace_id=trace_id,
            #         event_type=OutboxEventType.EMAIL_AUTH_CODE,
            #         aggregate_type="user",
            #         aggregate_id=user.id,
            #         outbox_fingerprint=outbox_fingerprint,
            #         payload={
            #             "user_id": user.id,
            #             "email_verification_id": email_verification.id,
            #             "verify_token": email_token,
            #         },
            #         status=OutboxStatus.PENDING,
            #         attempts=0,
            #     ),
            #     True,
            # )

            uow.commit()

            return {"ok": True}

    def verify_email(
        self,
        *,
        token: str,
    ) -> None:
        now = utcnow()

        token_hash = self._hmac.token_hash(token)

        with self._uow_factory() as uow:

            email_verification = uow.users.get_email_verification_by_token_hash(
                token_hash
            )

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
        trace_id = get_trace_id()
        expires_at = now + timedelta(minutes=self._config.access_token_minutes)

        with self._uow_factory() as uow:
            user = uow.users.get_by_user_id(user_id)
            if not user:
                raise ValidationAppError("User not found", target="user_id")

            if not self._password.verify_password(current_password, user.password_hash):
                raise ValidationAppError(
                    "Current password is incorrect", target="current_password"
                )

            new_email_fingerprint = self._hmac.fp_hash(new_email)
            new_email_secrets = self._secrets.encrypt(new_email.encode("utf-8"))
            if uow.users.get_user_by_email_fingerprint(new_email_fingerprint):
                raise ValidationAppError(
                    "email_fingerprint already exists", target="new_email"
                )

            self._enqueue_email_auth_code_outbox_in_tx(
                uow=uow,
                trace_id=trace_id,
                user_id=user.id,
                email_fingerprint=new_email_fingerprint,
                email_ciphertext=new_email_secrets["ciphertext"],
                email_nonce=new_email_secrets["nonce"],
                email_key_version=self._config.crypto_data_kid,
                expires_at=expires_at,
                cancel_pending=True,
                now=now,
            )
            # email_token = self._jwt.create_access_token(
            #     subject=str(user.id), minutes=self._config.access_token_minutes
            # )

            # email_verification = uow.users.add_email_verification(
            #     UserDTO.EmailVerificationCreate(
            #         user_id=user.id,
            #         email_fingerprint=new_email_fingerprint,
            #         email_ciphertext=new_email_secrets["ciphertext"],
            #         email_nonce=new_email_secrets["nonce"],
            #         email_key_version=self._config.crypto_data_kid,
            #         token_hash=self._hmac.token_hash(email_token),
            #         expires_at=expires_at,
            #     )
            # )

            # outbox_fingerprint_dict = {
            #     "event_type": OutboxEventType.EMAIL_AUTH_CODE,
            #     "aggregate_type": "user",
            #     "aggregate_id": user.id,
            #     "email_verification_id": email_verification.id,
            # }
            # outbox_fingerprint = to_canonical_json(outbox_fingerprint_dict)
            # if outbox_fingerprint is not None:
            #     outbox_fingerprint = self._hmac.fp_hash(outbox_fingerprint)

            # uow.outboxs.add_outbox(
            #     OutboxDTO.OutboxCreate(
            #         trace_id=trace_id,
            #         event_type=OutboxEventType.EMAIL_AUTH_CODE,
            #         aggregate_type="user",
            #         aggregate_id=user.id,
            #         outbox_fingerprint=outbox_fingerprint,
            #         payload={
            #             "user_id": user.id,
            #             "email_verification_id": email_verification.id,
            #             "verify_token": email_token,
            #         },
            #         status=OutboxStatus.PENDING,
            #         attempts=0,
            #     ),
            #     True,
            # )

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
