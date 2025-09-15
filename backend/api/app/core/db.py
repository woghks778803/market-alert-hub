from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.core import settings
from typing import Iterator

engine = create_engine(settings.SQLALCHEMY_URL, pool_pre_ping=True, future=True)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False, future=True)


# 의존성 주입용 DB 세션
def get_db() -> Iterator[Session]:
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except:  # noqa: E722
        db.rollback()
        raise
    finally:
        db.close()
