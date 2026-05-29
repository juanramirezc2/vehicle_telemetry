from collections.abc import AsyncIterator
from datetime import datetime

from fastapi.testclient import TestClient

from backend.app.core.database import get_session
from backend.app.main import create_app
from backend.app.models import TelemetryEvent


class FakeResult:
    def __init__(self, rows: list[TelemetryEvent]) -> None:
        self.rows = rows

    def scalars(self) -> list[TelemetryEvent]:
        return self.rows


class FakeSession:
    def __init__(self, rows: list[TelemetryEvent] | None = None) -> None:
        self.rows = rows or []

    async def execute(self, statement: object) -> FakeResult:
        return FakeResult(self.rows)


def anomaly_event(
    *,
    event_id: str,
    vehicle_id: str = "v-12",
    battery_pct: float = 78,
    speed_mps: float = 1.2,
    timestamp: datetime = datetime(2026, 5, 28, 12, 0, 0),
) -> TelemetryEvent:
    return TelemetryEvent(
        id=event_id,
        vehicle_id=vehicle_id,
        timestamp=timestamp,
        received_at=datetime(2026, 5, 28, 12, 0, 1),
        lat=37.41,
        lon=-122.08,
        battery_pct=battery_pct,
        speed_mps=speed_mps,
        status="moving",
        error_codes=[],
        zone_entered=None,
    )


def make_client(session: FakeSession) -> TestClient:
    app = create_app(enable_lifespan=False)

    async def override_get_session() -> AsyncIterator[FakeSession]:
        yield session

    app.dependency_overrides[get_session] = override_get_session
    return TestClient(app)


def test_list_anomalies_returns_derived_reasons() -> None:
    session = FakeSession(
        [
            anomaly_event(event_id="low", battery_pct=4.9),
            anomaly_event(event_id="fast", speed_mps=5.1),
            anomaly_event(event_id="both", battery_pct=4.9, speed_mps=5.1),
        ]
    )
    client = make_client(session)

    response = client.get("/api/anomalies?limit=3")

    assert response.status_code == 200
    body = response.json()
    assert [event["id"] for event in body] == ["low", "fast", "both"]
    assert body[0]["reasons"] == ["low_battery"]
    assert body[1]["reasons"] == ["overspeed"]
    assert body[2]["reasons"] == ["low_battery", "overspeed"]


def test_list_anomalies_accepts_utc_z_time_range() -> None:
    client = make_client(FakeSession([anomaly_event(event_id="low", battery_pct=4.9)]))

    response = client.get(
        "/api/anomalies?start=2026-05-28T12:00:00Z&end=2026-05-28T12:05:00.123Z"
    )

    assert response.status_code == 200


def test_list_anomalies_rejects_invalid_limit() -> None:
    client = make_client(FakeSession())

    response = client.get("/api/anomalies?limit=0")

    assert response.status_code == 422


def test_list_anomalies_rejects_timestamp_without_z() -> None:
    client = make_client(FakeSession())

    response = client.get("/api/anomalies?start=2026-05-28T12:00:00")

    assert response.status_code == 422


def test_list_anomalies_rejects_offset_timestamp() -> None:
    client = make_client(FakeSession())

    response = client.get("/api/anomalies?end=2026-05-28T12:00:00+00:00")

    assert response.status_code == 422
