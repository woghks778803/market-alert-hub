import base64

from datetime import timedelta
from secrets import token_bytes
from typing import Dict, Any

import jwt  # PyJWT

from app.core.datetime_utils import utcnow
from app.domain import CryptoPort


def _b64url_random(nbytes: int = 16) -> str:
    return base64.urlsafe_b64encode(token_bytes(nbytes)).rstrip(b"=").decode("ascii")


class JwtTokenSigner(CryptoPort.TokenSigner):
    """
    TokenSignerPort 구현 (PyJWT 기반).

    - 기본 알고리즘: HS256 (대칭키)
    - 서명키: init 시 직접 전달하거나, 환경변수에서 가져옴 (ACCESS_TOKEN_SECRET 또는 JWT_SECRET)
    - 만료시간 기본값: default_minutes (미지정 시 60분)
    - 검증 시 iss/aud가 지정되어 있으면 필수로 검증
    - token_hash: SHA-256 (기본) 또는 HMAC-SHA256 (pepper 존재 시)
    - consteq: 상수시간 비교
    """

    def __init__(
        self,
        *,
        secret: str,
        algorithm: str = "HS256",
        issuer: str | None = None,
        audience: str | None = None,
        default_minutes: int = 60,
        leeway_seconds: int = 0,
    ) -> None:
        # 서명용 비밀키: 우선 인자, 없으면 ENV
        self._secret = secret
        if not self._secret:
            raise RuntimeError(
                "ACCESS_TOKEN_SECRET (or JWT_SECRET) is not set and no secret was provided."
            )
        self._algorithm = algorithm
        self._issuer = issuer
        self._audience = audience
        self._default_minutes = default_minutes
        self._leeway = leeway_seconds

    def create_access_token(
        self,
        subject: str | int,
        *,
        minutes: int | None = None,
        claims: Dict[str, Any] | None = None,
    ) -> str:
        now = utcnow()
        exp_minutes = minutes if minutes is not None else self._default_minutes
        payload: Dict[str, Any] = {
            "sub": str(subject),
            "iat": int(now.timestamp()),
            "nbf": int(now.timestamp()),
            "exp": int((now + timedelta(minutes=exp_minutes)).timestamp()),
            "jti": _b64url_random(16),  # 128-bit 난수 식별자
        }
        if self._issuer:
            payload["iss"] = self._issuer
        if self._audience:
            payload["aud"] = self._audience

        # 추가 클레임 병합(표준 키 충돌 시 추가 클레임이 덮어쓰지 않도록 보호)
        if claims:
            for k, v in claims.items():
                if k in ("sub", "iat", "nbf", "exp", "jti", "iss", "aud"):
                    continue
                payload[k] = v

        token = jwt.encode(payload, self._secret, algorithm=self._algorithm)
        # PyJWT v2: str 반환(HS 계열), v1 호환성은 고려하지 않음
        return token

    def decode_token(self, token: str) -> Dict[str, Any]:
        options = {
            "require": ["exp", "iat", "nbf", "sub"],
        }
        kwargs: Dict[str, Any] = {
            "algorithms": [self._algorithm],
            "options": options,
            "leeway": self._leeway,
        }
        if self._issuer:
            kwargs["issuer"] = self._issuer
        if self._audience:
            kwargs["audience"] = self._audience

        # 검증 + 디코드
        decoded = jwt.decode(token, self._secret, **kwargs)  # type: ignore[arg-type]
        # PyJWT는 dict 반환
        return decoded  # type: ignore[return-value]
