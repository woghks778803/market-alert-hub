from urllib.parse import quote_plus
from pydantic import computed_field, Field, EmailStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
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

    # --- JWT ---
    JWT_SECRET: str = "change-me"
    JWT_ALG: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 360

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


settings = Settings()
