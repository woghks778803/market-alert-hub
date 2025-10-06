from urllib.parse import quote_plus
from pydantic import computed_field, Field, EmailStr
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # deploy
    DEPLOY_ENV : str = "dev"

    # --- DB ---
    MYSQL_HOST: str
    MYSQL_PORT: int = 3306
    MYSQL_DATABASE: str
    MYSQL_USER: str
    MYSQL_PASSWORD: str

    # --- JWT ---
    JWT_SECRET: str = "change-me"
    JWT_ALG: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 360

    # SES
    aws_region: str = Field(default="ap-northeast-2")
    ses_from_email: EmailStr
    ses_configuration_set: str | None = None  # 없으면 None
    # 네트워크/보안: 기본은 IAM Role 사용 권장. 로컬 개발 시만 키 사용.
    aws_access_key_id: str | None = None
    aws_secret_access_key: str | None = None

    # 로컬 개발 편의: .env 읽기 (컨테이너에선 ENV가 우선)
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,   # MYSQL_HOST / mysql_host 둘 다 허용
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

settings = Settings()
