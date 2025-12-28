from typing import Optional, Mapping, Dict

from app.domain import CryptoPort
from app.infra.external.crypto.local_aesgcm import LocalAesGcmCrypto


class LocalAesGcmFromSecrets(CryptoPort.SecretCrypto):
    """
    AWS Secrets Manager에서 마스터키를 읽어 LocalAesGcmCrypto로 위임하는 구현.
    필요 권한: secretsmanager:GetSecretValue (및 암호화에 사용된 KMS에 대한 권한은 Secrets Manager가 처리)
    """

    def __init__(self, inner: LocalAesGcmCrypto):
        self._inner = inner

    # SecretCryptoPort 구현 위임
    def encrypt(
        self,
        plaintext: bytes,
        *,
        aad: Optional[Mapping[str, str]] = None,
    ) -> Mapping[str, bytes]:
        return self._inner.encrypt(plaintext, aad=aad)

    def decrypt(
        self,
        *,
        ciphertext: bytes,
        nonce: bytes,
        aad: Optional[Mapping[str, str]] = None,
        kms_encrypted_dek: Optional[bytes] = None,  # 인터페이스 호환(미사용)
    ) -> bytes:
        return self._inner.decrypt(
            ciphertext=ciphertext, nonce=nonce, aad=aad, kms_encrypted_dek=None
        )
