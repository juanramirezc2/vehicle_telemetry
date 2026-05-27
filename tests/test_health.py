from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.app.core.config import Settings
from backend.app.main import create_app


async def passing_check(app: FastAPI) -> None:
    return None


async def failing_check(app: FastAPI) -> None:
    raise RuntimeError("service unavailable")


def test_root_returns_api_metadata() -> None:
    client = TestClient(create_app(enable_lifespan=False))

    response = client.get("/")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_settings_parse_comma_separated_cors_origins() -> None:
    settings = Settings(cors_origins="http://localhost:5173, http://localhost:3000")

    assert settings.cors_origins == [
        "http://localhost:5173",
        "http://localhost:3000",
    ]


def test_health_endpoint() -> None:
    client = TestClient(create_app(enable_lifespan=False))

    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_database_health_success() -> None:
    client = TestClient(
        create_app(database_check=passing_check, enable_lifespan=False)
    )

    response = client.get("/api/health/db")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_database_health_failure() -> None:
    client = TestClient(
        create_app(database_check=failing_check, enable_lifespan=False)
    )

    response = client.get("/api/health/db")

    assert response.status_code == 503
    assert response.json() == {"detail": "Database health check failed"}


def test_redis_health_success() -> None:
    client = TestClient(
        create_app(redis_check=passing_check, enable_lifespan=False)
    )

    response = client.get("/api/health/redis")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_redis_health_failure() -> None:
    client = TestClient(
        create_app(redis_check=failing_check, enable_lifespan=False)
    )

    response = client.get("/api/health/redis")

    assert response.status_code == 503
    assert response.json() == {"detail": "Redis health check failed"}
