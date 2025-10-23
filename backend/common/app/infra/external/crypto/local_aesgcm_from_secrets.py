import base64
import json
import os
from typing import Optional, Mapping, Dict

import boto3
from botocore.exceptions import ClientError

# 도메인 포트 / 로컬 AESGCM 구현
from app.domain import CryptoPort
from app.infra.external.crypto.local_aesgcm import LocalAesGcmCrypto


def _parse_key(raw: str) -> bytes:
    """
    base64 → hex → utf-8 순으로 파싱. 길이는 16/24/32 바이트만 허용.
    """
    # base64
    try:
        k = base64.b64decode(raw, validate=True)
        if len(k) in (16, 24, 32):
            return k
    except Exception:
        pass
    # hex
    try:
        k = bytes.fromhex(raw)
        if len(k) in (16, 24, 32):
            return k
    except Exception:
        pass
    # utf-8 raw
    k = raw.encode("utf-8")
    if len(k) not in (16, 24, 32):
        raise RuntimeError("Invalid AES key length (need 16/24/32 bytes via base64/hex/raw).")
    return k


def _extract_secret_value(secret_resp: Dict, json_key: Optional[str]) -> str:
    """
    Secrets Manager GetSecretValue 응답에서 키 문자열 추출.
    - SecretString: 그대로 사용. JSON이면 json_key로 선택.
    - SecretBinary: base64 디코드 후 utf-8로 변환(키가 바이너리면 그대로 base64 문자열을 키로 쓰는 것을 권장).
    """
    if "SecretString" in secret_resp and secret_resp["SecretString"] is not None:
        s = secret_resp["SecretString"]
        if json_key:
            try:
                obj = json.loads(s)
            except json.JSONDecodeError as e:
                raise RuntimeError(f"SecretString is not valid JSON while json_key='{json_key}' specified: {e}")
            if json_key not in obj:
                raise RuntimeError(f"json_key '{json_key}' not found in SecretString JSON.")
            val = obj[json_key]
            if not isinstance(val, str):
                raise RuntimeError(f"json_key '{json_key}' must map to a string.")
            return val
        return s

    if "SecretBinary" in secret_resp and secret_resp["SecretBinary"] is not None:
        try:
            # SecretBinary는 base64-encoded bytes
            b = base64.b64decode(secret_resp["SecretBinary"])
            # 바이너리 키를 그대로 쓰고 싶다면 base64 문자열을 키로 쓰는 게 안전하지만,
            # 여기서는 관례상 텍스트 기반 키라고 가정하고 utf-8로 변환 시도.
            return b.decode("utf-8")
        except Exception as e:
            raise RuntimeError(f"Failed to decode SecretBinary: {e}")

    raise RuntimeError("Secret has neither SecretString nor SecretBinary.")


class LocalAesGcmFromSecrets(CryptoPort.SecretCrypto):
    """
    AWS Secrets Manager에서 마스터키를 읽어 LocalAesGcmCrypto로 위임하는 구현.
    필요 권한: secretsmanager:GetSecretValue (및 암호화에 사용된 KMS에 대한 권한은 Secrets Manager가 처리)
    """

    def __init__(self, inner: LocalAesGcmCrypto):
        self._inner = inner

    # @classmethod
    # def from_secrets(
    #     cls,
    #     secret_id: str,
    #     *,
    #     region_name: Optional[str] = None,
    #     json_key: Optional[str] = None,
    #     boto3_client_kwargs: Optional[Dict] = None,
    # ) -> "LocalAesGcmFromSecrets":
    #     kms = boto3.client("secretsmanager", region_name=region_name, **(boto3_client_kwargs or {}))
    #     try:
    #         resp = kms.get_secret_value(SecretId=secret_id)
    #     except ClientError as e:
    #         raise RuntimeError(f"Failed to get secret '{secret_id}': {e}")

    #     raw_value = _extract_secret_value(resp, json_key)
    #     key_bytes = _parse_key(raw_value)
    #     return cls(LocalAesGcmCrypto(master_key=key_bytes))

    # @classmethod
    # def from_env(cls) -> "LocalAesGcmFromSecrets":
    #     """
    #     환경변수:
    #       - SECRET_ID (필수): Secrets Manager의 SecretId
    #       - SECRET_JSON_KEY (선택): SecretString이 JSON일 때 키 이름
    #       - AWS_REGION (선택): 리전 지정(미설정 시 boto3 기본값)
    #     """
    #     secret_id = os.environ.get("SECRET_ID")
    #     if not secret_id:
    #         raise RuntimeError("SECRET_ID not set (Secrets Manager SecretId).")
    #     json_key = os.environ.get("SECRET_JSON_KEY")
    #     region = os.environ.get("AWS_REGION")
    #     return cls.from_secrets(secret_id=secret_id, region_name=region, json_key=json_key)

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
        return self._inner.decrypt(ciphertext=ciphertext, nonce=nonce, aad=aad, kms_encrypted_dek=None)
