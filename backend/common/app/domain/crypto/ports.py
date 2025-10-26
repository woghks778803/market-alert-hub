from typing import Protocol, Mapping, Dict, Any


class SecretCrypto(Protocol):
    """
    앱 레벨 비밀(예: 외부 API Key/Secret) 암복호화 포트.
    구현 예: AES-GCM(+KMS 봉투암호).
    """

    def encrypt(
        self,
        plaintext: bytes,
        *,
        aad: Mapping[str, str] | None = None,
    ) -> Mapping[str, bytes]:
        ...
        """
        반환 예:
        {
          "ciphertext": b"...",
          "nonce": b"...",
          # KMS 사용 시:
          # "kms_encrypted_dek": b"...",
        }
        """

    def decrypt(
        self,
        *,
        ciphertext: bytes,
        nonce: bytes,
        aad: Mapping[str, str] | None = None,
        kms_encrypted_dek: bytes | None = None,
    ) -> bytes:
        ...
        """암호문 복호화 → 평문 반환"""


class PasswordHasher(Protocol):
    """
    사용자 비밀번호 해시/검증 포트.
    구현 예: passlib(bcrypt/argon2).
    """

    def hash_password(self, plain: str) -> str: ...

    def verify_password(self, plain: str, hashed: str) -> bool: ...


class TokenSigner(Protocol):
    """
    액세스 토큰(JWT 등) 생성/검증/지문 해시 포트.
    - token_hash: create_access_token 결과(토큰 문자열)를 해시해 DB에 저장/조회용 지문 생성
      (기본 SHA-256, 구현체에 따라 pepper를 써서 HMAC-SHA256로 강화 가능)
    - consteq: 상수시간 비교(타이밍 공격 완화)
    """

    def create_access_token(
        self,
        subject: str | int,
        *,
        minutes: int | None = None,
        claims: Dict[str, Any] | None = None,
    ) -> str: ...

    def decode_token(self, token: str) -> Dict[str, Any]: ...

    def token_hash(self, token: str) -> str:
        """
        DB/블랙리스트/세션 추적용 지문.
        구현체는 SHA-256 또는 HMAC-SHA256(pepper) 중 정책에 맞게 선택.
        반환은 64-hex 고정 길이를 권장.
        """
        ...

    def consteq(self, a: str, b: str) -> bool:
        """
        토큰 지문 비교 시 상수시간 비교 제공.
        """
        ...


class TokenFingerprint(Protocol):
    """
    API 키 등 '원문 저장 없이 식별/중복검사'용 지문 포트.
    구현 예: HMAC-SHA256(pepper 포함).
    """

    def fingerprint(self, value_utf8: str) -> str: ...

    def last4(self, value_utf8: str) -> str: ...
