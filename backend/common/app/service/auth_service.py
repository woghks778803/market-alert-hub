import secrets
import json
from typing import Callable, Dict, Any
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode
from app.core.constants import (
    UserRole,
    UserStatus,
    OutboxStatus,
    EmailVerificationStatus,
    OutboxEventType,
    OAuthCode,
    OAuthResultType,
    ChannelCode
)
from app.core import dto as CoreDTO
from app.core.util.trace import get_trace_id
from app.core.util.datetime import utcnow, ensure_utc
from app.core.util.serialization import to_canonical_json
from app.domain.shared.uow import UnitOfWork
from app.domain.shared.errors import (
    NotFoundError,
    ValidationAppError,
    PermissionError,
    ConflictError,
    AuthError,
    RateLimitError,
    InternalServerError,
)
from app.domain import (
    OutboxDTO,
    UserDTO,
    AuthDTO,
    EmailDTO,
    CryptoPort,
    AuthPort,
    AuthRule,
    ThrottlePort,
)


class AuthService:
    def __init__(
        self,
        *,
        cooldown: ThrottlePort.Cooldown,
        state: AuthPort.AuthState,
        kakao_oauth: AuthPort.KakaoOAuth,
        uow_factory: Callable[[], UnitOfWork],
        password: CryptoPort.PasswordHasher,
        hmac: CryptoPort.TokenHasher,
        jwt: CryptoPort.TokenSigner,
        secrets: CryptoPort.SecretCrypto,
        config: CoreDTO.ServiceConfigBag,
    ) -> None:
        self._cooldown = cooldown
        self._state = state
        self._uow_factory = uow_factory
        self._kakao_oauth = kakao_oauth
        self._password = password
        self._hmac = hmac
        self._jwt = jwt
        self._secrets = secrets
        self._config = config

    def _enqueue_email_auth_code_outbox_in_tx(
        self,
        *,
        uow: UnitOfWork,
        trace_id: str,
        user_id: int,
        email_fingerprint: bytes,
        email_ciphertext: bytes,
        email_nonce: bytes,
        email_key_version: int,
        cancel_pending: bool = False,
        now: datetime,
    ) -> AuthDTO.EmailVerificationEnqueueResult:
        """
        트랜잭션 내부 전용 공통 함수.
        """
        now = now
        email_expires_at = now + timedelta(minutes=self._config.email_token_minutes)

        # pending/sent 취소
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
        email_token = self._jwt.create_token(
            subject=str(user_id),
            minutes=self._config.email_token_minutes,
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
                expires_at=email_expires_at,
            )
        )

        # 3) outbox fingerprint (중복 방지)
        fp_dict: dict[str, Any] = {
            "event_type": OutboxEventType.AUTH_EMAIL_VERIFY,
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
                event_type=OutboxEventType.AUTH_EMAIL_VERIFY,
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
            expires_at=email_expires_at,
            outbox_fingerprint=outbox_fingerprint,
        )

    def reissue_token(
        self, *, refresh_token: str, ip: str | None = None, ua: str | None = None
    ) -> AuthDTO.AuthToken:
        now = utcnow()
        refresh_expires_at = now + timedelta(minutes=self._config.refresh_token_minutes)

        with self._uow_factory() as uow:
            s = uow.sessions.get_session_by_hash(self._hmac.token_hash(refresh_token))
            if not s:
                raise AuthError("Invalid token", target="refresh_token")

            if s.revoked_at is not None or ensure_utc(s.expires_at) <= now:
                uow.sessions.update_session_revoke(
                    user_id=s.user_id, revoked_at=now, token_hash=s.token_hash
                )
                raise AuthError("Expired token", target="refresh_token")

            user = uow.users.get_by_user_id(s.user_id)
            if not user:
                raise AuthError("Invalid token", target="refresh_token")

            access_token = self._jwt.create_token(
                subject=str(user.id),
                minutes=self._config.access_token_minutes,
                claims={
                    "ev": bool(user.email_verified_at),
                    "ee": bool(
                        user.email_fingerprint is not None
                        and user.email_ciphertext is not None
                        and user.email_nonce is not None
                        and user.email_key_version is not None
                    ),
                    "role": user.role.value,
                },
            )

            # new_refresh_token = secrets.token_urlsafe(48)
            # uow.sessions.add_session(
            #     user_id=user.id,
            #     token_hash=self._hmac.token_hash(new_refresh_token),
            #     expires_at=refresh_expires_at,
            #     ip_addr=ip,
            #     user_agent=ua,
            # )

            # # 기존 세션 무효화
            # uow.sessions.update_session(self._hmac.token_hash(refresh_token))

            uow.commit()

            return AuthDTO.AuthToken(
                access_token=access_token, refresh_token=refresh_token
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

        refresh_expires_at = now + timedelta(minutes=self._config.refresh_token_minutes)

        with self._uow_factory() as uow:
            email_fingerprint = self._hmac.fp_hash(email)
            email_secrets = self._secrets.encrypt(email.encode("utf-8"))

            user = uow.users.get_user_by_email_fingerprint(email_fingerprint)

            if user:
                if user.status == UserStatus.DELETED:
                    raise PermissionError(
                        "User status deleted", target="status.deleted"
                    )
                elif user.status == UserStatus.SUSPENDED:
                    raise PermissionError(
                        "User status suspended", target="status.suspended"
                    )

                raise ConflictError("email_fingerprint already exists", target="email")

            user = uow.users.add_user(
                UserDTO.UserCreate(
                    email_fingerprint=email_fingerprint,
                    email_ciphertext=email_secrets["ciphertext"],
                    email_nonce=email_secrets["nonce"],
                    email_key_version=self._config.crypto_data_kid,
                    nickname=nickname,
                    password_hash=self._password.hash_password(password),
                    last_login_at=now,
                    is_service=agree_service,
                    is_privacy=agree_privacy,
                    is_marketing=agree_marketing,
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
                cancel_pending=False,
                now=now,
            )

            access_token = self._jwt.create_token(
                subject=str(user.id),
                minutes=self._config.access_token_minutes,
                claims={
                    "ev": bool(user.email_verified_at),
                    "ee": bool(
                        user.email_fingerprint is not None
                        and user.email_ciphertext is not None
                        and user.email_nonce is not None
                        and user.email_key_version is not None
                    ),
                    "role": user.role.value,
                },
            )

            refresh_token = secrets.token_urlsafe(48)
            uow.sessions.add_session(
                user_id=user.id,
                token_hash=self._hmac.token_hash(refresh_token),
                expires_at=refresh_expires_at,
                ip_addr=ip,
                user_agent=ua,
            )

            uow.commit()

            return AuthDTO.AuthToken(
                access_token=access_token, refresh_token=refresh_token
            )

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
        refresh_expires_at = now + timedelta(minutes=self._config.refresh_token_minutes)

        with self._uow_factory() as uow:
            email_fingerprint = self._hmac.fp_hash(email)
            user = uow.users.get_user_by_email_fingerprint(email_fingerprint)
            if not user:
                raise NotFoundError("User not found", target="user")

            if user.status == UserStatus.DELETED:
                raise PermissionError("User status deleted", target="status.deleted")
            elif user.status == UserStatus.SUSPENDED:
                raise PermissionError(
                    "User status suspended", target="status.suspended"
                )

            if user.password_hash is None or not self._password.verify_password(
                password, user.password_hash
            ):
                raise AuthError("Invalid credentials", target="user")

            if admin_chk == True and user.role != UserRole.ADMIN:
                raise PermissionError("Admin role required", target="role")

            if user.email_verified_at is None:
                cooldown_sec = self._config.email_resend_cooldown_sec
                key = f"email_verify_resend:{user.id}"
                ok = self._cooldown.acquire(key, cooldown_sec)
                if ok:
                    if (
                        user.email_fingerprint is not None
                        and user.email_ciphertext is not None
                        and user.email_nonce is not None
                        and user.email_key_version is not None
                    ):
                        self._enqueue_email_auth_code_outbox_in_tx(
                            uow=uow,
                            trace_id=get_trace_id(),
                            user_id=user.id,
                            email_fingerprint=user.email_fingerprint,
                            email_ciphertext=user.email_ciphertext,
                            email_nonce=user.email_nonce,
                            email_key_version=user.email_key_version,
                            cancel_pending=True,
                            now=now,
                        )
                    else:
                        # 이메일 가입자 - 관리자 문의
                        raise AuthError(
                            "Account email data missing. Contact support.",
                            target="email",
                        )

            access_token = self._jwt.create_token(
                subject=str(user.id),
                minutes=self._config.access_token_minutes,
                claims={
                    "ev": bool(user.email_verified_at),
                    "ee": bool(
                        user.email_fingerprint is not None
                        and user.email_ciphertext is not None
                        and user.email_nonce is not None
                        and user.email_key_version is not None
                    ),
                    "role": user.role.value,
                },
            )

            refresh_token = secrets.token_urlsafe(48)
            uow.sessions.add_session(
                user_id=user.id,
                token_hash=self._hmac.token_hash(refresh_token),
                expires_at=refresh_expires_at,
                ip_addr=ip,
                user_agent=ua,
            )

            uow.users.update_user_last_login_at(user.id, now)
            uow.commit()

            return AuthDTO.AuthToken(
                access_token=access_token, refresh_token=refresh_token
            )

    # 로그아웃 (세션 무효화)
    def logout(self, *, user_id: int, refresh_token: str) -> Dict[str, Any]:
        now = utcnow()
        with self._uow_factory() as uow:
            user = uow.users.get_by_user_id(user_id)
            if not user:
                raise AuthError("Invalid credentials", target="user")

            uow.sessions.update_session_revoke(
                user_id=user_id, revoked_at=now, token_hash=self._hmac.token_hash(refresh_token)
            )
            uow.commit()
            return {"ok": True}

    def send_email_verification(
        self,
        *,
        user_id: int,
    ) -> Dict[str, Any]:
        now = utcnow()
        trace_id = get_trace_id()

        with self._uow_factory() as uow:
            user = uow.users.get_by_user_id(user_id)
            if not user:
                raise AuthError("Invalid credentials", target="user")

            if user.email_verified_at is not None:
                raise ConflictError("Email already verified", target="email")

            #  쿨다운 (연타 방지)
            cooldown_sec = self._config.email_resend_cooldown_sec
            key = f"email_verify_resend:{user.id}"
            ok = self._cooldown.acquire(key, cooldown_sec)
            if not ok:
                remain = self._cooldown.remain(key)  # -2/-1 처리만 조심
                raise RateLimitError(
                    "Too many requests. Please try again later.",
                    target="resend_email_verification",
                    meta={"cooldown_remaining_sec": max(remain, 0)},
                )

            if (
                user.email_fingerprint is not None
                and user.email_ciphertext is not None
                and user.email_nonce is not None
                and user.email_key_version is not None
            ):
                self._enqueue_email_auth_code_outbox_in_tx(
                    uow=uow,
                    trace_id=trace_id,
                    user_id=user.id,
                    email_fingerprint=user.email_fingerprint,
                    email_ciphertext=user.email_ciphertext,
                    email_nonce=user.email_nonce,
                    email_key_version=user.email_key_version,
                    cancel_pending=True,
                    now=now,
                )
            else:
                # TODO: 소셜 가입자 여부 - 이메일 등록 페이지로 유도
                # 이메일 가입자 - 관리자 문의
                raise AuthError(
                    "Account email data missing. Contact support.",
                    target="email",
                )

            uow.commit()

            return {"ok": True}

    def verify_email(
        self,
        *,
        token: str,
    ) -> str:
        now = utcnow()

        token_hash = self._hmac.token_hash(token)

        with self._uow_factory() as uow:
            email_verification = uow.users.get_email_verification_by_token_hash(
                token_hash
            )

            build_path = {
                "code": "success",
            }

            if not email_verification:
                return urlencode({"code": "not_found", "target": "token"})

            if email_verification.status != EmailVerificationStatus.SENT:
                return urlencode({"code": "validation_error", "target": "status"})

            expires_at = ensure_utc(email_verification.expires_at)
            if expires_at <= now:
                return urlencode({"code": "validation_error", "target": "token"})

            user = uow.users.get_by_user_id(email_verification.user_id)
            if not user:
                return urlencode({"code": "not_found", "target": "user"})

            uow.users.update_user_email_verified_at(
                id=user.id,
                email_verified_at=now,
            )
            uow.users.update_email_verification_by_filter(
                filters=EmailDTO.EmailVerificationFilter(id=email_verification.id),
                updates=EmailDTO.EmailVerificationUpdate(
                    status=EmailVerificationStatus.CONSUMED,
                    consumed_at=now,
                ),
            )

            uow.commit()

            return urlencode(build_path)

    def change_email(
        self, 
        *, 
        user_id: int, 
        new_email: str, 
        # current_password: str | None = None,
        ip: str | None = None,
        ua: str | None = None,
    ) -> str:
        now = utcnow()
        trace_id = get_trace_id()

        with self._uow_factory() as uow:
            user = uow.users.get_by_user_id(user_id)
            if not user:
                raise AuthError("Invalid credentials", target="user")

            # if user.password_hash is None or not self._password.verify_password(
            #     current_password, user.password_hash
            # ):
            #     raise AuthError("Invalid credentials", target="user")

            new_email_fingerprint = self._hmac.fp_hash(new_email)
            new_email_secrets = self._secrets.encrypt(new_email.encode("utf-8"))
            if uow.users.get_user_by_email_fingerprint(new_email_fingerprint):
                raise ConflictError(
                    "email_fingerprint already exists", target="new_email"
                )

            #  쿨다운 (연타 방지)
            cooldown_sec = self._config.email_resend_cooldown_sec
            key = f"email_verify_resend:{user.id}"
            ok = self._cooldown.acquire(key, cooldown_sec)
            if not ok:
                remain = self._cooldown.remain(key)  # -2/-1 처리만 조심
                raise RateLimitError(
                    "Too many requests. Please try again later.",
                    target="resend_email_verification",
                    meta={"cooldown_remaining_sec": max(remain, 0)},
                )

            self._enqueue_email_auth_code_outbox_in_tx(
                uow=uow,
                trace_id=trace_id,
                user_id=user.id,
                email_fingerprint=new_email_fingerprint,
                email_ciphertext=new_email_secrets["ciphertext"],
                email_nonce=new_email_secrets["nonce"],
                email_key_version=self._config.crypto_data_kid,
                cancel_pending=True,
                now=now,
            )

            uow.users.update_user_email(
                id=user.id,
                email_fingerprint=new_email_fingerprint,
                email_ciphertext=new_email_secrets["ciphertext"],
                email_nonce=new_email_secrets["nonce"],
                email_key_version=self._config.crypto_data_kid,
            )

            access_token = self._jwt.create_token(
                subject=str(user.id),
                minutes=self._config.access_token_minutes,
                claims={
                    "ev": bool(user.email_verified_at),
                    "ee": bool(
                        new_email_fingerprint is not None
                        and new_email_secrets["ciphertext"] is not None
                        and new_email_secrets["nonce"] is not None
                        and self._config.crypto_data_kid is not None
                    ),
                    "role": user.role.value,
                },
            )

            uow.commit()

            return access_token

    def send_password_reset(
        self,
        *,
        email: str,
    ):
        now = utcnow()
        trace_id = get_trace_id()
        email_expires_at = now + timedelta(minutes=self._config.email_token_minutes)

        with self._uow_factory() as uow:
            email_fingerprint = self._hmac.fp_hash(email)
            user = uow.users.get_user_by_email_fingerprint(email_fingerprint)
            if not user:
                raise AuthError("Invalid credentials", target="email")

            #  쿨다운 (연타 방지)
            cooldown_sec = self._config.email_resend_cooldown_sec
            key = f"email_verify_resend:{user.id}"
            ok = self._cooldown.acquire(key, cooldown_sec)
            if not ok:
                remain = self._cooldown.remain(key)  # -2/-1 처리만 조심
                raise RateLimitError(
                    "Too many requests. Please try again later.",
                    target="resend_password_reset",
                    meta={"cooldown_remaining_sec": max(remain, 0)},
                )

            password_token = self._jwt.create_token(
                subject=str(user.id),
                minutes=self._config.email_token_minutes,
            )
            password_reset = uow.users.add_password_reset(
                UserDTO.PasswordResetCreate(
                    user_id=user.id,
                    token_hash=self._hmac.token_hash(password_token),
                    expires_at=email_expires_at,
                )
            )

            outbox_fingerprint_dict = {
                "event_type": OutboxEventType.AUTH_PASSWORD_RESET,
                "aggregate_type": "user",
                "aggregate_id": user.id,
                "password_reset_id": password_reset.id,
            }

            outbox_fingerprint = to_canonical_json(outbox_fingerprint_dict)
            if outbox_fingerprint is not None:
                outbox_fingerprint = self._hmac.fp_hash(outbox_fingerprint)

            uow.outboxs.add_outbox(
                OutboxDTO.OutboxCreate(
                    trace_id=trace_id,
                    event_type=OutboxEventType.AUTH_PASSWORD_RESET,
                    aggregate_type="user",
                    aggregate_id=user.id,
                    outbox_fingerprint=outbox_fingerprint,
                    payload={
                        "user_id": user.id,
                        "password_reset_id": password_reset.id,
                        "verify_token": password_token,
                    },
                    status=OutboxStatus.PENDING,
                    attempts=0,
                ),
                True,
            )

            uow.commit()
            return {"ok": True}

    def change_password(self, *, user_id: int, current_password: str, new_password: str):
        now = utcnow()
        with self._uow_factory() as uow:
            user = uow.users.get_by_user_id(user_id)
            if not user:
                raise AuthError("Invalid credentials", target="user")

            if user.password_hash is None or not self._password.verify_password(
                current_password, user.password_hash
            ):
                raise PermissionError("Invalid credentials", target="user")

            uow.users.update_user_password_hash(
                id=user.id, password_hash=self._password.hash_password(new_password)
            )

            chp = uow.channels.get_provider_by_code(ChannelCode.FCM.value)
            if not chp:
                raise NotFoundError(
                    "Not found channel provider", target="channel_provider"
                )
            if not chp.is_active:
                raise ValidationAppError(
                    "Channel provider is not active", target="channel_provider"
                )

            uow.channels.update_channel_active(
                channel_provider_id=chp.id,
                user_id=user.id,
                is_active=False
            )
            uow.sessions.update_session_revoke(user_id=user_id, revoked_at=now)

            uow.commit()

            return {"ok": True}

    def reset_password(self, *, token: str, new_password: str):
        now = utcnow()
        token_hash = self._hmac.token_hash(token)

        with self._uow_factory() as uow:
            password_reset = uow.users.get_password_reset_by_token_hash(
                token_hash, consumed_is_null=True, expires_after=now
            )
            if not password_reset:
                raise NotFoundError("Token not found", target="token")

            expires_at = ensure_utc(password_reset.expires_at)
            if expires_at <= now:
                raise ValidationAppError("Token expired", target="token")

            user = uow.users.get_by_user_id(password_reset.user_id)
            if not user:
                raise NotFoundError("User not found", target="user")

            uow.users.update_user_password_hash(
                id=user.id, password_hash=self._password.hash_password(new_password)
            )

            uow.users.update_password_reset_by_filter(
                id=password_reset.id,
                expires_after=now,
                consumed_at=now,
                sent_is_null=False,
                consumed_is_null=True,
            )

            chp = uow.channels.get_provider_by_code(ChannelCode.FCM.value)
            if not chp:
                raise NotFoundError(
                    "Not found channel provider", target="channel_provider"
                )
            if not chp.is_active:
                raise ValidationAppError(
                    "Channel provider is not active", target="channel_provider"
                )

            uow.channels.update_channel_active(
                channel_provider_id=chp.id,
                user_id=user.id,
                is_active=False
            )
            uow.sessions.update_session_revoke(user_id=user.id, revoked_at=now)

            uow.commit()

            return {"ok": True}

    def verify_password_reset(self, *, token: str):
        now = utcnow()
        token_hash = self._hmac.token_hash(token)
        with self._uow_factory() as uow:
            password_reset = uow.users.get_password_reset_by_token_hash(
                token_hash, consumed_is_null=True, expires_after=now
            )
            if not password_reset:
                raise NotFoundError("Token not found", target="token")

            expires_at = ensure_utc(password_reset.expires_at)
            if expires_at <= now:
                raise ValidationAppError("Token expired", target="token")

            return {"ok": True}

    def get_current_user(self, user_id: int, token: str) -> AuthDTO.AuthUser:
        now = utcnow()
        with self._uow_factory() as uow:

            user = uow.users.get_by_user_id(user_id)
            if not user:
                raise AuthError("Invalid credentials", target="token")

            # 세션 유효성(선택이지만 권장)
            s = uow.sessions.get_session_by_hash(
                self._hmac.token_hash(token),
            )
            if s is None:
                raise AuthError("Invalid credentials", target="token")

            expires_at = ensure_utc(s.expires_at)
            revoked_at = s.revoked_at
            if revoked_at is not None and revoked_at.tzinfo is None:
                revoked_at = revoked_at.replace(tzinfo=timezone.utc)

            if not s or revoked_at or expires_at <= now:
                raise AuthError("Missing or invalid token", target="token")

            return AuthDTO.AuthUser(access_token=token, id=user.id, role=user.role)

    def oauth_start(
        self,
        provider: str,
        agree_service: bool | None,
        agree_privacy: bool | None,
        agree_marketing: bool | None,
    ) -> AuthDTO.OAuthResult:
        with self._uow_factory() as uow:
            provider = provider.upper()
            oauth_provider = uow.users.get_oauth_provider_by_code(
                code=provider, is_active=True
            )

            if oauth_provider is None:
                return AuthDTO.OAuthResult(
                    result_type=OAuthResultType.ERROR,
                    authorize_path=urlencode(
                        {
                            "source": provider,
                            "code": "not_found",
                            "target": "oauth_provider",
                        }
                    )
                )

        # state 저장 위치/정책에 맞게 구현
        # - redis 사용 시: key= f"oauth:state:{provider}:{state}"
        # - value에 created_at, provider 정도 저장
        # - TTL (예: 300초)
        value_dict = {
            "provider": provider,
            "agree_service": agree_service,
            "agree_privacy": agree_privacy,
            "agree_marketing": agree_marketing,
        }

        try:
            state = self._state.create(
                "oauth", value_dict, self._config.oauth_state_sec
            )
        except RuntimeError:
            return AuthDTO.OAuthResult(
                result_type=OAuthResultType.ERROR,
                authorize_path=urlencode(
                    {"source": provider, "code": "internal_error", "target": "state"}
                )
            )

        return AuthDTO.OAuthResult(
            result_type=OAuthResultType.SUCCESS,
            authorize_path=self._kakao_oauth.build_authorize_path(state=state)
        )

    def oauth_callback(
        self,
        # provider: str,
        code: str,
        state: str,
        error: str,
        ip: str | None = None,
        ua: str | None = None,
    ):
        now = utcnow()
        is_enroll_email = False
        is_verify_email = False

        data = self._state.consume("oauth", state)

        if data == None:  # key not exist
            return AuthDTO.OAuthResult(
                result_type=OAuthResultType.ERROR,
                authorize_path=urlencode(
                    {
                        "source": None,
                        "code": "validation_error",
                        "target": "state",
                    }
                )
            )

        provider = data["provider"]
        agree_service = data["agree_service"]
        agree_privacy = data["agree_privacy"]
        agree_marketing = data["agree_marketing"]

        if error:
            return AuthDTO.OAuthResult(
                result_type=OAuthResultType.ERROR,
                authorize_path=urlencode(
                    {
                        "source": provider,
                        "code": error,
                        "target": "oauth",
                    }
                )
            )

        if not code or not state:
            return AuthDTO.OAuthResult(
                result_type=OAuthResultType.ERROR,
                authorize_path=urlencode(
                    {
                        "source": provider,
                        "code": "invalid_request",
                        "target": "oauth",
                    }
                )
            )

        with self._uow_factory() as uow:
            oauth_provider = uow.users.get_oauth_provider_by_code(
                code=provider, is_active=True
            )

            if oauth_provider is None:
                return AuthDTO.OAuthResult(
                    result_type=OAuthResultType.ERROR,
                    authorize_path=urlencode(
                        {
                            "source": provider,
                            "code": "not_found",
                            "target": "oauth",
                        }
                    )
                )

        # 3) provider client로 사용자 식별 정보 가져오기
        # - kakao_oauth.fetch_identity(code) -> AuthDto.Identity
        oauth_identity = self._kakao_oauth.fetch_identity(code)

        with self._uow_factory() as uow:
            oauth_account = uow.users.get_oauth_account_by_filter(
                oauth_provider_id=oauth_provider.id,
                provider_user_id=oauth_identity.provider_user_id,
            )
            if oauth_account:
                user = uow.users.get_by_user_id(
                    oauth_account.user_id, deleted_is_null=False
                )

                if user is None:
                    return AuthDTO.OAuthResult(
                        result_type=OAuthResultType.ERROR,
                        authorize_path=urlencode(
                            {
                                "source": provider,
                                "code": "internal_error",
                                "target": "user",
                            }
                        )
                    )

                if user.status == UserStatus.DELETED:
                    return AuthDTO.OAuthResult(
                        result_type=OAuthResultType.ERROR,
                        authorize_path=urlencode(
                            {
                                "source": provider,
                                "code": "forbidden",
                                "target": "status.deleted",
                            }
                        )
                    )
                elif user.status == UserStatus.SUSPENDED:
                    return AuthDTO.OAuthResult(
                        result_type=OAuthResultType.ERROR,
                        authorize_path=urlencode(
                            {
                                "source": provider,
                                "code": "forbidden",
                                "target": "status.suspended",
                            }
                        )
                    )

                uow.users.update_user_last_login_at(id=user.id, last_login_at=now)
            else:
                if not agree_service or not agree_privacy:
                    return AuthDTO.OAuthResult(
                        result_type=OAuthResultType.TERMS_REQUIRED,
                        authorize_path=urlencode(
                            {
                                "source": provider,
                            }
                        )
                    )

                user = uow.users.add_user(
                    UserDTO.UserCreate(
                        nickname=oauth_identity.nickname
                        or AuthRule.generate_default_nickname(),
                        last_login_at=now,
                        is_service=agree_service,
                        is_privacy=agree_privacy,
                        is_marketing=agree_marketing,
                    )
                )
                uow.users.add_user_oauth_account(
                    UserDTO.UserOAuthAccountCreate(
                        user_id=user.id,
                        oauth_providers_id=oauth_provider.id,
                        provider_user_id=oauth_identity.provider_user_id,
                        linked_at=now,
                    )
                )

            # token 발급
            refresh_expires_at = now + timedelta(
                minutes=self._config.refresh_token_minutes
            )
            refresh_token = secrets.token_urlsafe(48)
            uow.sessions.add_session(
                user_id=user.id,
                token_hash=self._hmac.token_hash(refresh_token),
                expires_at=refresh_expires_at,
                ip_addr=ip,
                user_agent=ua,
            )

            access_token = self._jwt.create_token(
                subject=str(user.id),
                minutes=self._config.access_token_minutes,
                claims={
                    "ev": bool(user.email_verified_at),
                    "ee": bool(
                        user.email_fingerprint is not None
                        and user.email_ciphertext is not None
                        and user.email_nonce is not None
                        and user.email_key_version is not None
                    ),
                    "role": user.role.value,
                },
            )

            uow.commit()

        authorize_path = urlencode(
            {
                "code": "ok"
            }
        )
        return AuthDTO.OAuthResult(
            result_type=OAuthResultType.SUCCESS,
            authorize_path=authorize_path,
            refresh_token=refresh_token,
            access_token=access_token,
        )

    def deactivate_user(self, *, user_id: int) -> None:
        now = utcnow()
        with self._uow_factory() as uow:
            user = uow.users.get_by_user_id(user_id)
            if not user:
                raise NotFoundError("User not found", target="user")

            # 외부 OAuth 연동 해제
            accounts = uow.users.list_oauth_accounts_by_user(
                user_id=user.id, unlinked_at_is_null=True
            )

            if accounts:

                def _unlink_kakao(provider_user_id: str) -> None:
                    self._kakao_oauth.unlink(int(provider_user_id))

                unlink_map = {
                    OAuthCode.KAKAO.value: _unlink_kakao,
                    # 다른 OAuth 프로바이더 추가 시 여기서 매핑
                }

                for account in accounts:
                    provider = uow.users.get_oauth_provider_by_id(
                        id=account.oauth_providers_id
                    )
                    if not provider:
                        continue
                    handler = unlink_map.get(provider.code)
                    if handler:
                        try:
                            handler(account.provider_user_id)
                        except Exception as e:
                            raise InternalServerError(
                                f"Failed to unlink {provider.code} account",
                                target="oauth",
                            ) from e

                uow.users.update_oauth_accounts_unlinked_at(
                    user_id=user.id, unlinked_at=now
                )

            chp = uow.channels.get_provider_by_code(ChannelCode.FCM.value)
            if not chp:
                raise NotFoundError(
                    "Not found channel provider", target="channel_provider"
                )
            if not chp.is_active:
                raise ValidationAppError(
                    "Channel provider is not active", target="channel_provider"
                )

            uow.channels.update_channel_active(
                channel_provider_id=chp.id,
                user_id=user.id,
                is_active=False
            )
            uow.users.delete_user(
                user_id=user.id, status=UserStatus.DELETED, deleted_at=now
            )
            uow.sessions.update_session_revoke(user_id=user.id, revoked_at=now)
            uow.users.update_user_email_verified_at(id=user.id)
            uow.commit()
