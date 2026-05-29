from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import create_async_engine

from backend.app.api.health import router as health_router
from backend.app.api.routes.anomalies import router as anomalies_router
from backend.app.api.routes.telemetry import router as telemetry_router
from backend.app.core.config import Settings, get_settings
from backend.app.core.database import SessionLocal
from backend.app.realtime import create_asgi_app
from backend.app.services.health import check_database, check_redis

HealthCheck = Callable[[FastAPI], Awaitable[None]]


def create_app(
    *,
    settings: Settings | None = None,
    database_check: HealthCheck = check_database,
    redis_check: HealthCheck = check_redis,
    enable_lifespan: bool = True,
) -> FastAPI:
    app_settings = settings or get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        if not enable_lifespan:
            yield
            return

        app.state.db_engine = create_async_engine(
            app_settings.database_url,
            pool_size=20,
            max_overflow=10,
            pool_pre_ping=True,
        )
        SessionLocal.configure(bind=app.state.db_engine)
        app.state.redis = Redis.from_url(app_settings.redis_url, decode_responses=True)
        try:
            yield
        finally:
            await app.state.redis.aclose()
            await app.state.db_engine.dispose()

    app = FastAPI(title=app_settings.project_name, lifespan=lifespan)
    app.state.settings = app_settings
    app.state.database_check = database_check
    app.state.redis_check = redis_check

    app.add_middleware(
        CORSMiddleware,
        allow_origins=app_settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health_router, prefix="/api")
    app.include_router(anomalies_router, prefix="/api")
    app.include_router(telemetry_router, prefix="/api")

    @app.get("/")
    async def root() -> dict[str, Any]:
        return {
            "name": app_settings.project_name,
            "environment": app_settings.environment,
            "status": "ok",
        }

    return app


fastapi_app = create_app()
app = create_asgi_app(fastapi_app, fastapi_app.state.settings)
