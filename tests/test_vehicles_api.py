from collections.abc import AsyncIterator
from datetime import datetime

from fastapi.testclient import TestClient

from backend.app.core.database import get_session
from backend.app.main import create_app
from backend.app.models import Vehicle


class FakeResult:
    def __init__(self, rows: list[Vehicle]) -> None:
        self.rows = rows

    def scalars(self) -> list[Vehicle]:
        return self.rows


class FakeSession:
    def __init__(self, rows: list[Vehicle] | None = None) -> None:
        self.rows = rows or []

    async def execute(self, statement: object) -> FakeResult:
        return FakeResult(self.rows)


def vehicle(
    *,
    vehicle_id: str,
    status: str = "moving",
    battery: float = 78,
    current_zone: str | None = "aisle_a",
) -> Vehicle:
    return Vehicle(
        id=vehicle_id,
        status=status,
        battery=battery,
        current_zone=current_zone,
        updated_at=datetime(2026, 5, 28, 12, 0, 0),
    )


def make_client(session: FakeSession) -> TestClient:
    app = create_app(enable_lifespan=False)

    async def override_get_session() -> AsyncIterator[FakeSession]:
        yield session

    app.dependency_overrides[get_session] = override_get_session
    return TestClient(app)


def test_list_vehicles_returns_all_vehicles() -> None:
    session = FakeSession(
        [
            vehicle(vehicle_id="v-1", status="moving", battery=82),
            vehicle(vehicle_id="v-2", status="fault", battery=3.2, current_zone=None),
        ]
    )
    client = make_client(session)

    response = client.get("/api/vehicles?limit=2")

    assert response.status_code == 200
    assert response.json() == [
        {
            "id": "v-1",
            "status": "moving",
            "battery": 82.0,
            "current_zone": "aisle_a",
            "updated_at": "2026-05-28T12:00:00",
        },
        {
            "id": "v-2",
            "status": "fault",
            "battery": 3.2,
            "current_zone": None,
            "updated_at": "2026-05-28T12:00:00",
        },
    ]


def test_list_vehicles_rejects_invalid_limit() -> None:
    client = make_client(FakeSession())

    response = client.get("/api/vehicles?limit=0")

    assert response.status_code == 422
