from collections.abc import AsyncIterator
from datetime import datetime
from uuid import UUID

from fastapi.testclient import TestClient
from sqlalchemy.exc import IntegrityError

from backend.app.core.database import get_session
from backend.app.main import create_app
from backend.app.models import TelemetryEvent


class FakeSession:
    def __init__(self, *, fail_commit: bool = False) -> None:
        self.fail_commit = fail_commit
        self.added: TelemetryEvent | None = None
        self.rolled_back = False

    def add(self, telemetry: TelemetryEvent) -> None:
        self.added = telemetry

    async def commit(self) -> None:
        if self.fail_commit:
            raise IntegrityError("insert telemetry", {}, Exception("foreign key"))

    async def rollback(self) -> None:
        self.rolled_back = True

    async def refresh(self, telemetry: TelemetryEvent) -> None:
        telemetry.received_at = datetime(2026, 5, 28, 12, 0, 1)


def valid_payload() -> dict[str, object]:
    return {
        "vehicle_id": "v-12",
        "timestamp": "2026-05-28T12:00:00",
        "lat": 37.41,
        "lon": -122.08,
        "battery_pct": 78,
        "speed_mps": 1.2,
        "status": "moving",
        "error_codes": [],
        "zone_entered": None,
    }


def make_client(session: FakeSession) -> TestClient:
    app = create_app(enable_lifespan=False)

    async def override_get_session() -> AsyncIterator[FakeSession]:
        yield session

    app.dependency_overrides[get_session] = override_get_session
    return TestClient(app)


def test_create_telemetry_event_returns_created_event() -> None:
    session = FakeSession()
    client = make_client(session)

    response = client.post("/api/telemetry", json=valid_payload())

    assert response.status_code == 201
    body = response.json()
    assert UUID(body["id"])
    assert body["vehicle_id"] == "v-12"
    assert body["status"] == "moving"
    assert body["zone_entered"] is None
    assert body["received_at"] == "2026-05-28T12:00:01"
    assert session.added is not None
    assert session.added.id == body["id"]


def test_create_telemetry_event_accepts_zone_entered() -> None:
    session = FakeSession()
    client = make_client(session)
    payload = valid_payload() | {"zone_entered": "charging_bay_1"}

    response = client.post("/api/telemetry", json=payload)

    assert response.status_code == 201
    assert response.json()["zone_entered"] == "charging_bay_1"


def test_create_telemetry_event_rejects_invalid_status() -> None:
    client = make_client(FakeSession())
    payload = valid_payload() | {"status": "offline"}

    response = client.post("/api/telemetry", json=payload)

    assert response.status_code == 422


def test_create_telemetry_event_rejects_invalid_zone() -> None:
    client = make_client(FakeSession())
    payload = valid_payload() | {"zone_entered": "unknown_zone"}

    response = client.post("/api/telemetry", json=payload)

    assert response.status_code == 422


def test_create_telemetry_event_rejects_invalid_battery() -> None:
    client = make_client(FakeSession())
    payload = valid_payload() | {"battery_pct": 101}

    response = client.post("/api/telemetry", json=payload)

    assert response.status_code == 422


def test_create_telemetry_event_returns_bad_request_for_invalid_vehicle() -> None:
    session = FakeSession(fail_commit=True)
    client = make_client(session)

    response = client.post("/api/telemetry", json=valid_payload())

    assert response.status_code == 400
    assert response.json() == {"detail": "Invalid vehicle_id"}
    assert session.rolled_back is True
