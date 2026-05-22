import asyncio, logging, sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi

from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from sqlalchemy.exc import IntegrityError
from app.domain.shared.errors import AppError

from app.core.constants import DeploymentEnvironment, CandleInterval, TickerInterval
from app.core.logging import setup_logging

from app.api.deps import get_api_context
from app.api.middleware import RequestIdMiddleware
from app.api.exception_handlers import unified_exception_handler
from app.api.router import api
from app.ws.deps import get_ws_context
from app.ws.router import ws
from app.ws.stores import MarketStore
from app.ws.hub import Hub

from app.ws.broadcasters.candle_broadcaster import (
    run_candle_broadcaster,
    run_candle_list_broadcaster,
)
from app.ws.broadcasters.ticker_broadcaster import (
    run_ticker_broadcaster,
    run_ticker_list_broadcaster,
)
from app.ws.consumers.candle_consumer import run_candle_consumer
from app.ws.consumers.ticker_consumer import run_ticker_consumer

api_ctx = get_api_context()
ws_ctx = get_ws_context()


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
    service_name = api_ctx.config.service_name
    deploy_env = api_ctx.config.deploy_env

    sentry_dsn = api_ctx.config.sentry_dsn
    sample_rate = api_ctx.config.sample_rate
    traces_sample_rate = api_ctx.config.traces_sample_rate

    cors_allow_origins = api_ctx.config.cors_allow_origins

    is_prod = deploy_env == DeploymentEnvironment.PROD
    is_local = deploy_env == DeploymentEnvironment.LOCAL
    
    setup_logging(
        level=logging.INFO if is_prod else logging.DEBUG,
        service=service_name,
    )

    app = FastAPI(
        title="Market Alert Hub API",
        description="실시간 크립토 알림 서비스의 백엔드 API",
        version="0.1.0",
        # openapi_tags=TAGS_METADATA,
        docs_url="/api/docs" if is_local else None,
        redoc_url=None, # "/api/redoc"
        openapi_url="/api/openapi.json" if is_local else None,
        swagger_ui_parameters={
            "docExpansion": "none",
            "defaultModelsExpandDepth": -1,
            "persistAuthorization": True,
        },
    )

    # 앱 전역 싱글톤 저장소 - 하나만 있어야 함
    app.state.ws_hub = Hub()
    app.state.ws_config = ws_ctx.config
    app.state.ws_svcs = ws_ctx.svcs
    app.state.market_store = MarketStore()
    app.state.candle_queue = asyncio.Queue()

    sentry_sdk.init(
        dsn=sentry_dsn,
        integrations=[FastApiIntegration()],
        environment=deploy_env,
        sample_rate=sample_rate,
        traces_sample_rate=traces_sample_rate,
        send_default_pii=True,
        # enable_logs=True,
    )
    sentry_sdk.set_tag("service", service_name)
    sentry_sdk.capture_message(f"sentry {service_name} connected")

    # --- Middleware ---
    # CORSMiddleware가 가장 바깥이어야함
    # ExceptionMiddleware는 FastAPI 기본 미들웨어라 따로 추가 안해도 됨
    app.add_middleware(RequestIdMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_allow_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # --- Exception Handlers ---
    # app.add_exception_handler(Exception, unified_exception_handler) # 이러면 StarletteHTTPException 등이 fastapi 생성시 기본값으로 할당되어서 안 거쳐감

    # --- Exception Handlers ---
    app.add_exception_handler(AppError, unified_exception_handler)                 # 도메인 에러
    app.add_exception_handler(StarletteHTTPException, unified_exception_handler)   # HTTPException
    app.add_exception_handler(RequestValidationError, unified_exception_handler)   # 바디/쿼리 검증 에러
    app.add_exception_handler(IntegrityError, unified_exception_handler)           # DB 무결성
    app.add_exception_handler(Exception, unified_exception_handler)                # 그 외 모든 것

    # --- Routers ---
    app.include_router(api)
    app.include_router(ws)

    @app.on_event("startup")
    async def startup():
        asyncio.create_task(run_candle_consumer(app, interval=CandleInterval.SEC_1))
        asyncio.create_task(run_candle_consumer(app, interval=CandleInterval.MIN_1))
        asyncio.create_task(run_candle_consumer(app, interval=CandleInterval.HOUR_1))
        asyncio.create_task(run_candle_consumer(app, interval=CandleInterval.DAY_1))

        asyncio.create_task(run_ticker_consumer(app, interval=TickerInterval.HOUR_24))

        asyncio.create_task(run_candle_broadcaster(app))
        asyncio.create_task(run_ticker_broadcaster(app))
        asyncio.create_task(run_candle_list_broadcaster(app))
        asyncio.create_task(run_ticker_list_broadcaster(app))

    # --- OpenAPI(Security) ---
    _install_openapi_with_bearer(app)

    return app


app = create_app()
