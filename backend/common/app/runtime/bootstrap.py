from .settings import settings
from app.core import dto as CoreDTO
from app.infra.external.email.ses_client import SesEmailClient
from app.infra.external.email.jinja_renderer import JinjaEmailRenderer
from app.infra.db.uow import UnitOfWork
from app.infra.db.engine import SessionLocal
from app.infra.external.password.passlib_hasher import PasslibPasswordHasher
from app.infra.external.token.jwt_signer import JwtTokenSigner
from app.infra.external.token.hmac_hasher import HmacTokenHasher
from app.infra.external.crypto.local_aesgcm import LocalAesGcmCrypto
from app.infra.external.crypto.local_aesgcm_from_secrets import LocalAesGcmFromSecrets
from app.service.factory import ServiceFactory
from typing import Callable

from passlib.context import CryptContext


def _load_master_key_from_aws() -> str:
    import json, base64  # boto3 응답 처리용
    import boto3

    sm = boto3.client("secretsmanager", region_name=settings.AWS_REGION)
    resp = sm.get_secret_value(SecretId=settings.CRYPTO_DATA_ENC_SECRET_ID)

    if "SecretString" in resp and resp["SecretString"] is not None:
        raw = resp["SecretString"]
        # JSON이면 키 추출
        if settings.CRYPTO_DATA_ENC_SECRET_FIELD:
            data = json.loads(raw)
            return str(data[settings.CRYPTO_DATA_ENC_SECRET_FIELD])
        return raw
    # Binary인 경우
    b = base64.urlsafe_b64decode(resp["SecretBinary"])
    return b.decode("utf-8")  # 네 구현이 문자열→키 파싱을 하므로 utf-8 가정


def _resolve_master_key() -> str:
    if settings.CRYPTO_DATA_ENC_SECRET_ID:
        return _load_master_key_from_aws()
    if settings.CRYPTO_DATA_ENC_KEY:
        return settings.CRYPTO_DATA_ENC_KEY
    raise RuntimeError(
        "Secret master key is not configured. "
        "Set CRYPTO_DATA_ENC_KEY or CRYPTO_DATA_ENC_SECRET_ID."
    )

class Providers:
    @staticmethod
    def email_client_provider() -> Callable[[], SesEmailClient]:
        return lambda: SesEmailClient()

    @staticmethod
    def email_renderer_provider() -> Callable[[], JinjaEmailRenderer]:
        return lambda: JinjaEmailRenderer()

    @staticmethod
    def create_uow_from_session(db_session) -> Callable[[], UnitOfWork]:
        return lambda: UnitOfWork(db_session, owns_session=True)

    @staticmethod
    def password_hasher_provider() -> Callable[[], PasslibPasswordHasher]:
        # 외부 옵션은 전부 settings에서만 읽음
        ctx = CryptContext(
            schemes=settings.PASSLIB_SCHEMES,
            deprecated=settings.PASSLIB_DEPRECATED,
            # argon2 옵션
            argon2__time_cost=settings.ARGON2_TIME_COST,
            argon2__memory_cost=settings.ARGON2_MEMORY_COST,
            argon2__parallelism=settings.ARGON2_PARALLELISM,
            # bcrypt 옵션
            bcrypt__rounds=settings.BCRYPT_ROUNDS,
        )

        return lambda: PasslibPasswordHasher(ctx)

    @staticmethod
    def jwt_signer_provider() -> Callable[[], JwtTokenSigner]:
        return lambda: JwtTokenSigner(
            secret=settings.JWT_SECRET,
            algorithm=settings.JWT_ALG,
            issuer=settings.JWT_ISSUER,
            audience=settings.JWT_AUDIENCE,
            default_minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
            leeway_seconds=settings.JWT_LEEWAY_SECONDS,
        )

    @staticmethod
    def hmac_hasher_provider() -> Callable[[], HmacTokenHasher]:
        return lambda: HmacTokenHasher(
            token_pepper=settings.TOKEN_MASTER_PEPPER,
            fp_pepper=settings.FP_MASTER_PEPPER,
        )

    @staticmethod
    def secret_crypto_provider() -> Callable[[], LocalAesGcmFromSecrets]:
        def _build():
            key = _resolve_master_key()
            inner = LocalAesGcmCrypto(
                master_key=key
            )  # 키 파싱/길이 검증은 내부에서 수행
            return LocalAesGcmFromSecrets(inner)  # 래퍼로 감싸 동일 인터페이스 제공

        return _build


providers = Providers()

def build_config_bag() -> CoreDTO.ConfigBag:
    return CoreDTO.ConfigBag(
        access_token_minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
        crypto_data_kid=settings.CRYPTO_DATA_ENC_KID,
        public_web_base_url=settings.PUBLIC_WEB_BASE_URL
    )

def create_service_factory(uow_provider: Callable[[], UnitOfWork]) -> ServiceFactory:

    return ServiceFactory(
        uow=uow_provider,
        email_client=providers.email_client_provider(),
        email_renderer=providers.email_renderer_provider(),
        password_hasher=providers.password_hasher_provider(),
        hmac_hasher=providers.hmac_hasher_provider(),
        jwt_signer=providers.jwt_signer_provider(),
        secret_crypto=providers.secret_crypto_provider(),
        config=build_config_bag(),
    )


def get_core_services() -> ServiceFactory:
    uow_provider = lambda: UnitOfWork(SessionLocal, owns_session=True)
    return create_service_factory(uow_provider)
