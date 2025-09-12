# 단일 Base만 선언해도 Alembic이 정상 동작합니다.
from sqlalchemy.orm import declarative_base

Base = declarative_base()

# (모델 추가 시)
# from app.model.base import Base

from .user import User
__all__ = ["User", "Alert"]