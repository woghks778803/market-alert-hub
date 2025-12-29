from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import sessionmaker, Session


def create_sqlalchemy_engine(sqlalchemy_url: str) -> Engine:
    # 여기서 settings import 금지. url은 외부(bootstrap)에서 주입
    return create_engine(sqlalchemy_url, pool_pre_ping=True, future=True)


def create_sessionmaker(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(
        bind=engine,
        autocommit=False,
        autoflush=False,
        future=True,
    )
