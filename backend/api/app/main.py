from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
import logging
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from app.core.constants import DeploymentEnvironment
from app.core.logging import setup_logging
from app.api.deps import get_app_context
from app.api.middleware import RequestIdMiddleware
from app.api.exception_handlers import unified_exception_handler
from app.api.router import api
from app.ws.router import ws
from app.ws.hub import Hub

ctx = get_app_context()


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
        # Swagger UI/Redoc에서 그룹 헤더처럼 보이게 하는 확장
        schema["x-tagGroups"] = [
            {
                "name": "Public",
                "tags": [],
            },
            {
                "name": "Admin",
                "tags": [],
            },
        ]
        # components = schema.setdefault("components", {})
        # security_schemes = components.setdefault("securitySchemes", {})
        # security_schemes["bearerAuth"] = {
        #     "type": "http",
        #     "scheme": "bearer",
        #     "bearerFormat": "JWT",
        # }
        # 전역 보안 적용을 원하면 아래 주석을 해제
        # schema["security"] = [{"bearerAuth": []}]
        app.openapi_schema = schema
        return app.openapi_schema

    app.openapi = custom_openapi  # type: ignore[assignment]


def create_app() -> FastAPI:
    if ctx.config.deploy_env == DeploymentEnvironment.PROD:
        setup_logging(level=logging.INFO, service="api")
    else:
        setup_logging(level=logging.DEBUG, service="api")

    app = FastAPI(
        title="Market Alert Hub API",
        description="실시간 크립토 알림 서비스의 백엔드 API",
        version="0.1.0",
        # openapi_tags=TAGS_METADATA,
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
        swagger_ui_parameters={
            "docExpansion": "none",
            "defaultModelsExpandDepth": -1,
            "persistAuthorization": True,
        },
    )

    # 앱 전역 싱글톤 저장소 - 하나만 있어야 함
    app.state.ws_hub = Hub()

    sentry_sdk.init(
        dsn=ctx.config.sentry_dsn,
        integrations=[FastApiIntegration()],
        environment=ctx.config.deploy_env,
        sample_rate=ctx.config.sample_rate,
        traces_sample_rate=ctx.config.traces_sample_rate,
        send_default_pii=True,
        # enable_logs=True,
    )
    sentry_sdk.set_tag("service", "api")
    sentry_sdk.capture_message("sentry api connected")

    # --- Middleware ---
    # CORSMiddleware가 가장 바깥이어야함
    # ExceptionMiddleware는 FastAPI 기본 미들웨어라 따로 추가 안해도 됨
    app.add_middleware(RequestIdMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=ctx.config.cors_allow_origins,  # TODO: 배포 시 도메인으로 제한
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # --- Exception Handlers ---
    app.add_exception_handler(Exception, unified_exception_handler)
    # --- Exception Handlers ---
    # app.add_exception_handler(AppError, unified_exception_handler)                 # 도메인 에러
    # app.add_exception_handler(StarletteHTTPException, unified_exception_handler)   # HTTPException
    # app.add_exception_handler(RequestValidationError, unified_exception_handler)   # 바디/쿼리 검증 에러
    # app.add_exception_handler(IntegrityError, unified_exception_handler)           # DB 무결성
    # app.add_exception_handler(Exception, unified_exception_handler)                # 그 외 모든 것

    # --- Routers ---
    app.include_router(api)
    app.include_router(ws)

    # --- OpenAPI(Security) ---
    _install_openapi_with_bearer(app)

    return app


app = create_app()
