from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import IntegrityError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.logging import setup_logging
from app.core.middleware import RequestIdMiddleware
from app.core.exception_handlers import (
    handle_app_error,
    handle_http_error,
    handle_validation_error,
    handle_integrity_error,
)
from app.core.errors import AppError
from app.router.public import health  # 헬스 라우터(아래 코드 참조)


def create_app() -> FastAPI:
    setup_logging()
    app = FastAPI(title="Market Alert Hub API")

    app.add_middleware(RequestIdMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 예외 핸들러
    app.add_exception_handler(AppError, handle_app_error)
    app.add_exception_handler(StarletteHTTPException, handle_http_error)
    from fastapi.exceptions import RequestValidationError

    app.add_exception_handler(RequestValidationError, handle_validation_error)
    app.add_exception_handler(IntegrityError, handle_integrity_error)

    # 라우터
    app.include_router(health.router, prefix="/api")

    return app


app = create_app()
