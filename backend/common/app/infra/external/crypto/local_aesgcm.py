import base64
from secrets import token_bytes
from typing import Mapping

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from app.domain import CryptoPort


def _canonical_aad(aad: Mapping[str, str] | None) -> bytes:
    """
    AAD 직렬화: 키 사전순 정렬 후 'k=v'를 '\n'으로 조인.
    - 암복호화 시 동일한 결과를 사용해야 복호화가 성공함.
    """
    if not aad:
        return b""
    parts = [f"{k}={aad[k]}" for k in sorted(aad.keys())]
    return "\n".join(parts).encode("utf-8")


def _parse_key(raw: str) -> bytes:
    """
    환경변수에서 전달된 키 문자열을 bytes로 파싱.
    우선 base64로 시도, 실패 시 hex, 그것도 아니면 UTF-8 raw를 사용.
    길이는 16/24/32 바이트(AES-128/192/256)만 허용.
    """
    # 1) base64
    try:
        k = base64.urlsafe_b64decode(raw)
        if len(k) in (16, 24, 32):
            return k
    except Exception:
        pass
    # 2) hex
    try:
        k = bytes.fromhex(raw)
        if len(k) in (16, 24, 32):
            return k
    except Exception:
        pass
    # 3) utf-8 raw
    k = raw.encode("utf-8")
    if len(k) not in (16, 24, 32):
        raise RuntimeError(
            "Invalid AES key length. Provide 16/24/32 bytes via base64, hex, or raw."
        )
    return k


class LocalAesGcmCrypto(CryptoPort.SecretCrypto):
    """
    로컬/개발/소규모 운영에서 사용할 수 있는 AES-GCM 구현.
    - 마스터키는 환경변수 등으로 주입.
    - 반환: {'ciphertext': bytes, 'nonce': bytes}
    - AESGCM.encrypt 반환에는 tag가 ciphertext에 포함됨.
    """

    def __init__(self, master_key: str):
        key = _parse_key(master_key)
        if len(key) not in (16, 24, 32):
            raise ValueError("AES key length must be 16/24/32 bytes")
        self._key = key

    def encrypt(
        self,
        plaintext: bytes,
        *,
        aad: Mapping[str, str] | None = None,
    ) -> Mapping[str, bytes]:
        # 모든 코드 경로에서 반환
        nonce = token_bytes(12)  # 96-bit nonce (GCM 권장)
        aesgcm = AESGCM(self._key)
        ct = aesgcm.encrypt(nonce, plaintext, _canonical_aad(aad))
        return {"ciphertext": ct, "nonce": nonce}

    def decrypt(
        self,
        *,
        ciphertext: bytes,
        nonce: bytes,
        aad: Mapping[str, str] | None = None,
        kms_encrypted_dek: bytes | None = None,  # 인터페이스 호환용(미사용)
    ) -> bytes:
        # kms_encrypted_dek는 로컬 구현에선 사용하지 않음.
        aesgcm = AESGCM(self._key)
        pt = aesgcm.decrypt(nonce, ciphertext, _canonical_aad(aad))
        return pt
