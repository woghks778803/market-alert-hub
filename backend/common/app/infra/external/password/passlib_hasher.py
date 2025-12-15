from passlib.context import CryptContext

from app.domain import CryptoPort


class PasslibPasswordHasher(CryptoPort.PasswordHasher):
    """
    PasswordHasherPort 구현 (passlib CryptContext 기반).

    기본 스킴:
      - argon2 (우선 적용)
      - bcrypt (백업/마이그레이션용)
    환경변수로 손쉽게 조정 가능:
      - PASSLIB_SCHEMES="argon2,bcrypt"  # 순서가 우선순위
      - PASSLIB_DEPRECATED="auto"        # 또는 "bcrypt"
      - ARGON2_TIME_COST=2
      - ARGON2_MEMORY_COST=102400
      - ARGON2_PARALLELISM=8
      - BCRYPT_ROUNDS=12
    """

    def __init__(self, ctx: CryptContext) -> None:
        self._ctx = ctx

    # === PasswordHasherPort 구현 ===

    def hash_password(self, plain: str) -> str:
        # 항상 문자열 반환(예외 발생 시 상위에서 처리)
        return self._ctx.hash(plain)

    def verify_password(self, plain: str, hashed: str) -> bool:
        return self._ctx.verify(plain, hashed)

    # 선택: 필요 시 서비스에서 사용할 수 있도록 제공 (Port에는 없음)
    def needs_rehash(self, hashed: str) -> bool:
        """
        해시가 현재 정책(스킴/라운드 등)에 맞지 않으면 True.
        로그인 성공 시 재해시/갱신에 사용 가능.
        """
        return self._ctx.needs_update(hashed)
