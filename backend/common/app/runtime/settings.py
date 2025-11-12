from urllib.parse import quote_plus
from pydantic import computed_field, field_validator, Field, EmailStr
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Any


class Settings(BaseSettings):

    def __init__(self, **data: Any):
        # ✅ Pylance에 "키워드 가변 인자 받는다"를 알려줘서 경고 제거
        super().__init__(**data)

    # deploy
    DEPLOY_ENV: str = "dev"

    # --- DB ---
    MYSQL_HOST: str
    MYSQL_PORT: int = 3306
    MYSQL_DATABASE: str
    MYSQL_USER: str
    MYSQL_PASSWORD: str

    # --- Redis ---
    REDIS_HOST: str = Field(default="redis")
    REDIS_PORT: int = Field(default=6379)
    REDIS_DB: int = Field(default=0)

    # --- version switch ---
    ACTIVE_JWT_KID: str = "v1"
    ACTIVE_TOKEN_PEPPER_VER: str = "h1"

    # --- JWT ---
    JWT_SECRET: str = "change-me"
    JWT_ALG: str = "HS256"
    JWT_ISSUER: str | None = None
    JWT_AUDIENCE: str | None = None
    JWT_LEEWAY_SECONDS: int = 0
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 360
    TOKEN_PEPPER: str = "ACCESS_TOKEN_PEPPER"

    # --- password ---
    ARGON2_TIME_COST: int = 2
    ARGON2_MEMORY_COST: int = 102_400
    ARGON2_PARALLELISM: int = 8
    BCRYPT_ROUNDS: int = 12

    PASSLIB_SCHEMES: str | list[str] = ["argon2", "bcrypt"]
    PASSLIB_DEPRECATED: str = "auto"

    # --- crypto ---
    CRYPTO_DATA_ENC_KEY_V1: str | None = None
    CRYPTO_DATA_ENC_SECRET_ID: str | None = None
    CRYPTO_DATA_ENC_SECRET_FIELD: str | None = (
        None  # 시크릿이 JSON이면 내부 키명 (예: "key")
    )

    # SES
    AWS_REGION: str = Field(default="ap-northeast-2")
    SES_FROM_EMAIL: EmailStr
    SES_CONFIGURATION_SET: str | None = None  # 없으면 None
    # 네트워크/보안: 기본은 IAM Role 사용 권장. 로컬 개발 시만 키 사용.
    AWS_ACCESS_KEY_ID: str | None = None
    AWS_SECRET_ACCESS_KEY: str | None = None

    # --- Worker 전용 ---
    LOG_LEVEL: str = Field(default="INFO")
    OUTBOX_POLL_LIMIT: int = Field(default=50)
    OUTBOX_IDLE_SLEEP: float = Field(default=1.0)
    OUTBOX_RETRY_DELAY_SEC: int = Field(default=60)
    OUTBOX_CONCURRENCY: int = Field(default=4)

    REDIS_STREAM_ALERTS: str = Field(default="alerts")
    REDIS_STREAM_DELIVERIES: str = Field(default="deliveries")

    # 로컬 개발 편의: .env 읽기 (컨테이너에선 ENV가 우선)
    model_config = SettingsConfigDict(
        # 환경변수가 없을 때만 주입
        # env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,  # MYSQL_HOST / mysql_host 둘 다 허용
        extra="ignore",
    )

    @computed_field  # pydantic v2
    @property
    def SQLALCHEMY_URL(self) -> str:
        pw = quote_plus(self.MYSQL_PASSWORD)  # 특수문자 안전
        return (
            f"mysql+pymysql://{self.MYSQL_USER}:{pw}"
            f"@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DATABASE}"
            f"?charset=utf8mb4"
        )

    @computed_field
    @property
    def REDIS_URL(self) -> str:
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    @field_validator("PASSLIB_SCHEMES", mode="before")
    def split_schemes(cls, v):
        if isinstance(v, str):
            return [x.strip() for x in v.split(",")]
        return v


settings = Settings()
