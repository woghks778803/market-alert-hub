import hmac
import hashlib
from app.domain import CryptoPort


class HmacTokenHasher(CryptoPort.TokenHasher):
    def __init__(self, *, token_pepper: str, fp_pepper: str) -> None:
        self._token_pepper = token_pepper
        self._fp_pepper = fp_pepper

    # === 지문/비교 ===
    def fp_hash(self, normalize: str) -> bytes:
        return self.hmac_hash(normalize, self._fp_pepper)

    def token_hash(self, token: str) -> bytes:
        return self.hmac_hash(token, self._token_pepper)

    def hmac_hash(self, data: str, pepper: str) -> bytes:
        """
        DB/블랙리스트/세션 추적용 지문.
        - HMAC-SHA256(pepper), 아니면 SHA-256
        - 64-hex 길이 반환
        """
        msg = data.encode("utf-8")
        if pepper:
            return hmac.new(pepper.encode("utf-8"), msg, hashlib.sha256).digest()
            # return hmac.new(pepper.encode("utf-8"), msg, hashlib.sha256).hexdigest()
        return hashlib.sha256(msg).digest()
        # return hashlib.sha256(msg).hexdigest()

    def consteq(self, a: str, b: str) -> bool:
        """상수시간 비교"""
        return hmac.compare_digest(a, b)
