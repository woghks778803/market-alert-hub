import ssl
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import sessionmaker, Session


def create_sqlalchemy_engine(sqlalchemy_url: str, pool_size: int, max_overflow: int, verify_tls: bool = False) -> Engine:
    connect_args = {}

    if verify_tls:
        connect_args["ssl"] = ssl.create_default_context()

    # 여기서 settings import 금지. url은 외부(bootstrap)에서 주입
    return create_engine(
        sqlalchemy_url, 
        pool_pre_ping=True, 
        pool_size=pool_size,
        max_overflow=max_overflow,
        connect_args=connect_args, # 인증서 검증
        future=True, # 2.0 방식 사용 옵션
        # pool_timeout=30
        # pool_recycle=1800
    )


def create_sessionmaker(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(
        bind=engine,
        autocommit=False,
        autoflush=False,
        future=True,
    )
