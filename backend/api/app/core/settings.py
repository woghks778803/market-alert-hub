import os


def _req(key: str) -> str:
    v = os.getenv(key)
    if not v:
        raise RuntimeError(f"Missing env: {key}")
    return v


class Settings:
    MYSQL_HOST = _req("MYSQL_HOST")
    MYSQL_PORT = _req("MYSQL_PORT")
    MYSQL_DB = _req("MYSQL_DATABASE")
    MYSQL_USER = _req("MYSQL_USER")
    MYSQL_PW = _req("MYSQL_PASSWORD")

    @property
    def SQLALCHEMY_URL(self) -> str:
        return f"mysql+pymysql://{self.MYSQL_USER}:{self.MYSQL_PW}@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DB}?charset=utf8mb4"


settings = Settings()
