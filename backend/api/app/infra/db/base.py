from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.settings import settings

engine = create_engine(
    settings.SQLALCHEMY_URL,
    future=True,
    pool_pre_ping=True,   # 죽은 커넥션 사전 감지
    pool_recycle=3600,    # MySQL 권장 (장기 유휴 커넥션 재생성)
    # echo=True,          # 필요 시 디버깅
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,  # 커밋 이후도 객체 필드 접근 가능
    future=True,
)

Base = declarative_base()
