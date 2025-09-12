# app/router/public/__init__.py
from fastapi import APIRouter
from . import health  # 필요한 모듈만 명시적으로

router = APIRouter(prefix="/api")   # ← 공통 prefix를 여기서
router.include_router(health.router)
# 라우터 추가 시 이 파일만 수정
