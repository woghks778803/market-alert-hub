import ssl
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

def create_async_sqlalchemy_engine(sqlalchemy_url: str, pool_size: int, max_overflow: int, verify_tls: bool = False) -> AsyncEngine:
    connect_args = {}

    if verify_tls:
        connect_args["ssl"] = ssl.create_default_context()

    return create_async_engine(
        sqlalchemy_url,
        pool_pre_ping=True,
        pool_size=pool_size,
        max_overflow=max_overflow,
        connect_args=connect_args, # 인증서 검증
        future=True,
    )

def create_async_sessionmaker(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(
        bind=engine,
        expire_on_commit=False,
        autoflush=False,
        autocommit=False,
    )