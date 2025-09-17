# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from sqlalchemy.exc import IntegrityError
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.exceptions import RequestValidationError

from app.core.logging import setup_logging
from app.api.middleware import RequestIdMiddleware
from app.api.exception_handlers import (
    handle_app_error,
    handle_http_error,
    handle_validation_error,
    handle_integrity_error,
)
from app.domain import AppError
from app.api.router import api

TAGS_METADATA = [
    {"name": "health", "description": "헬스체크/진단"},
    {"name": "auth", "description": "회원가입 · 로그인 · 토큰"},
]


def _install_openapi_with_bearer(app: FastAPI) -> None:
    """Swagger에 JWT Bearer 인증 스키마(bearerAuth) 추가."""
    def custom_openapi():
        if app.openapi_schema:
            return app.openapi_schema
        schema = get_openapi(
            title=app.title,
            version=app.version,
            description=app.description,
            routes=app.routes,
        )
        components = schema.setdefault("components", {})
        security_schemes = components.setdefault("securitySchemes", {})
        security_schemes["bearerAuth"] = {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        }
        # 전역 보안 적용을 원하면 아래 주석을 해제
        # schema["security"] = [{"bearerAuth": []}]
        app.openapi_schema = schema
        return app.openapi_schema

    app.openapi = custom_openapi  # type: ignore[assignment]


def create_app() -> FastAPI:
    setup_logging()

    app = FastAPI(
        title="Market Alert Hub API",
        description="실시간 크립토 알림 서비스의 백엔드 API",
        version="0.1.0",
        openapi_tags=TAGS_METADATA,
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
        swagger_ui_parameters={
            "docExpansion": "none",
            "defaultModelsExpandDepth": -1,
            "persistAuthorization": True,
        },
    )

    # --- Middleware ---
    app.add_middleware(RequestIdMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],                 # TODO: 배포 시 도메인으로 제한
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # --- Exception Handlers ---
    app.add_exception_handler(AppError, handle_app_error)
    app.add_exception_handler(StarletteHTTPException, handle_http_error)
    app.add_exception_handler(RequestValidationError, handle_validation_error)
    app.add_exception_handler(IntegrityError, handle_integrity_error)

    # --- Routers ---
    app.include_router(api)

    # --- OpenAPI(Security) ---
    _install_openapi_with_bearer(app)

    return app


app = create_app()
