from collections.abc import AsyncIterator
from datetime import datetime
from uuid import UUID

from fastapi.testclient import TestClient
from backend.app.core.database import get_session
from backend.app.main import create_app
from backend.app.models import MaintenanceRecord, TelemetryEvent, Vehicle
from backend.app.realtime import create_asgi_app
from backend.app.services.telemetry_service import InvalidVehicleError


class FakeResult:
    def __init__(self, rows: list[object], scalar: object | None = None) -> None:
        self.rows = rows
        self.scalar = scalar

    def scalars(self) -> list[object]:
        return self.rows

    def scalar_one(self) -> object:
        if self.scalar is None:
            raise AssertionError("Expected scalar result")
        return self.scalar

    def scalar_one_or_none(self) -> object | None:
        return self.scalar


class FakeTransaction:
    async def __aenter__(self) -> None:
        return None

    async def __aexit__(self, *args: object) -> None:
        return None


class FakeSession:
    def __init__(
        self,
        *,
        execute_rows: list[TelemetryEvent] | None = None,
        inserted_battery_pct: float = 78,
        inserted_speed_mps: float = 1.2,
        inserted_status: str = "moving",
        inserted_zone_entered: str | None = None,
        vehicle_status: str | None = "moving",
        fail_commit: bool = False,
    ) -> None:
        self.execute_rows = execute_rows or []
        self.inserted_battery_pct = inserted_battery_pct
        self.inserted_speed_mps = inserted_speed_mps
        self.inserted_status = inserted_status
        self.inserted_zone_entered = inserted_zone_entered
        self.vehicle = (
            Vehicle(
                id="v-12",
                status=vehicle_status,
                battery=78,
                current_zone=None,
                updated_at=datetime(2026, 5, 28, 12, 0, 0),
            )
            if vehicle_status is not None
            else None
        )
        self.fail_commit = fail_commit
        self.added: TelemetryEvent | None = None
        self.maintenance_records: list[MaintenanceRecord] = []
        self.cancelled_active_missions = 0
        self.locked_vehicle = False
        self.rolled_back = False

    async def execute(self, statement: object) -> FakeResult:
        if self.fail_commit:
            raise InvalidVehicleError

        if hasattr(statement, "is_insert") and statement.is_insert:
            values = valid_payload() | {
                "timestamp": datetime(2026, 5, 28, 12, 0, 0, 740000),
                "battery_pct": self.inserted_battery_pct,
                "speed_mps": self.inserted_speed_mps,
                "status": self.inserted_status,
                "zone_entered": self.inserted_zone_entered,
            }
            telemetry = TelemetryEvent(
                id="00000000-0000-4000-8000-000000000001",
                received_at=datetime(2026, 5, 28, 12, 0, 1),
                **values,
            )
            self.added = telemetry
            return FakeResult([], scalar=telemetry)

        table_names = [table.name for table in getattr(statement, "columns_clause_froms", [])]
        if "vehicles" in table_names:
            statement_text = str(statement)
            self.locked_vehicle = "FOR UPDATE" in statement_text.upper()
            return FakeResult([], scalar=self.vehicle)

        if hasattr(statement, "is_update") and statement.is_update:
            statement_text = str(statement)
            if "missions" in statement_text:
                self.cancelled_active_missions += 1
            return FakeResult([])

        return FakeResult(self.execute_rows)

    def begin(self) -> FakeTransaction:
        return FakeTransaction()

    def add(self, item: object) -> None:
        if isinstance(item, MaintenanceRecord):
            self.maintenance_records.append(item)
            return

        self.added = item

    async def commit(self) -> None:
        if self.fail_commit:
            raise IntegrityError("insert telemetry", {}, Exception("foreign key"))

    async def rollback(self) -> None:
        self.rolled_back = True

    async def refresh(self, telemetry: TelemetryEvent) -> None:
        telemetry.received_at = datetime(2026, 5, 28, 12, 0, 1)


class FakeSocketServer:
    def __init__(self) -> None:
        self.emitted: list[tuple[str, object]] = []

    async def emit(self, event: str, data: object) -> None:
        self.emitted.append((event, data))


def valid_payload() -> dict[str, object]:
    return {
        "vehicle_id": "v-12",
        "timestamp": "2026-05-28T12:00:00.740Z",
        "lat": 37.41,
        "lon": -122.08,
        "battery_pct": 78,
        "speed_mps": 1.2,
        "status": "moving",
        "error_codes": [],
        "zone_entered": None,
    }


def telemetry_event(
    *,
    event_id: str,
    vehicle_id: str,
    timestamp: datetime,
) -> TelemetryEvent:
    return TelemetryEvent(
        id=event_id,
        vehicle_id=vehicle_id,
        timestamp=timestamp,
        received_at=datetime(2026, 5, 28, 12, 0, 1),
        lat=37.41,
        lon=-122.08,
        battery_pct=78,
        speed_mps=1.2,
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


def make_client_with_socket(
    session: FakeSession,
    socket_server: FakeSocketServer,
) -> TestClient:
    app = create_app(enable_lifespan=False)
    app.state.socketio = socket_server

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
    assert body["timestamp"] == "2026-05-28T12:00:00.740000"
    assert body["status"] == "moving"
    assert body["zone_entered"] is None
    assert body["received_at"] == "2026-05-28T12:00:01"
    assert session.added is not None
    assert session.added.id == body["id"]


def test_list_telemetry_events_returns_latest_raw_events() -> None:
    session = FakeSession(
        execute_rows=[
            telemetry_event(
                event_id="event-2",
                vehicle_id="v-2",
                timestamp=datetime(2026, 5, 28, 12, 0, 2),
            ),
            telemetry_event(
                event_id="event-1",
                vehicle_id="v-1",
                timestamp=datetime(2026, 5, 28, 12, 0, 1),
            ),
        ]
    )
    client = make_client(session)

    response = client.get("/api/telemetry?limit=2")

    assert response.status_code == 200
    assert [event["id"] for event in response.json()] == ["event-2", "event-1"]


def test_list_telemetry_events_rejects_invalid_limit() -> None:
    client = make_client(FakeSession())

    response = client.get("/api/telemetry?limit=0")

    assert response.status_code == 422


def test_list_latest_events_by_vehicle_returns_one_event_per_vehicle() -> None:
    session = FakeSession(
        execute_rows=[
            telemetry_event(
                event_id="event-v-1",
                vehicle_id="v-1",
                timestamp=datetime(2026, 5, 28, 12, 0, 2),
            ),
            telemetry_event(
                event_id="event-v-2",
                vehicle_id="v-2",
                timestamp=datetime(2026, 5, 28, 12, 0, 1),
            ),
        ]
    )
    client = make_client(session)

    response = client.get("/api/events")

    assert response.status_code == 200
    assert [event["vehicle_id"] for event in response.json()] == ["v-1", "v-2"]


def test_create_telemetry_event_accepts_zone_entered() -> None:
    session = FakeSession(inserted_zone_entered="charging_bay_1")
    client = make_client(session)
    payload = valid_payload() | {"zone_entered": "charging_bay_1"}

    response = client.post("/api/telemetry", json=payload)

    assert response.status_code == 201
    assert response.json()["zone_entered"] == "charging_bay_1"


def test_create_telemetry_event_broadcasts_created_event() -> None:
    session = FakeSession()
    socket_server = FakeSocketServer()
    client = make_client_with_socket(session, socket_server)

    response = client.post("/api/telemetry", json=valid_payload())

    assert response.status_code == 201
    assert socket_server.emitted == [
        (
            "telemetry:created",
            {
                "id": response.json()["id"],
                "vehicle_id": "v-12",
                "timestamp": "2026-05-28T12:00:00.740000",
                "lat": 37.41,
                "lon": -122.08,
                "battery_pct": 78.0,
                "speed_mps": 1.2,
                "status": "moving",
                "error_codes": [],
                "zone_entered": None,
                "received_at": "2026-05-28T12:00:01",
            },
        )
    ]


def test_create_fault_telemetry_cancels_mission_and_opens_maintenance() -> None:
    session = FakeSession(inserted_status="fault")
    client = make_client(session)
    payload = valid_payload() | {"status": "fault", "error_codes": ["E_NAV_LOST"]}

    response = client.post("/api/telemetry", json=payload)

    assert response.status_code == 201
    assert session.locked_vehicle is True
    assert session.vehicle is not None
    assert session.vehicle.status == "fault"
    assert session.cancelled_active_missions == 1
    assert len(session.maintenance_records) == 1
    assert session.maintenance_records[0].vehicle_id == "v-12"
    assert session.maintenance_records[0].reason == "fault telemetry event"
    assert session.maintenance_records[0].triggering_event_id == response.json()["id"]


def test_create_fault_telemetry_is_idempotent_when_vehicle_already_fault() -> None:
    session = FakeSession(inserted_status="fault", vehicle_status="fault")
    client = make_client(session)
    payload = valid_payload() | {"status": "fault"}

    response = client.post("/api/telemetry", json=payload)

    assert response.status_code == 201
    assert session.locked_vehicle is True
    assert session.cancelled_active_missions == 0
    assert session.maintenance_records == []


def test_create_telemetry_event_broadcasts_low_battery_anomaly() -> None:
    session = FakeSession(inserted_battery_pct=4.9)
    socket_server = FakeSocketServer()
    client = make_client_with_socket(session, socket_server)
    payload = valid_payload() | {"battery_pct": 4.9}

    response = client.post("/api/telemetry", json=payload)

    assert response.status_code == 201
    assert socket_server.emitted[1] == (
        "anomaly:detected",
        {
            "id": response.json()["id"],
            "vehicle_id": "v-12",
            "timestamp": "2026-05-28T12:00:00.740000",
            "lat": 37.41,
            "lon": -122.08,
            "battery_pct": 4.9,
            "speed_mps": 1.2,
            "status": "moving",
            "error_codes": [],
            "zone_entered": None,
            "received_at": "2026-05-28T12:00:01",
            "reasons": ["low_battery"],
        },
    )


def test_create_telemetry_event_broadcasts_overspeed_anomaly() -> None:
    session = FakeSession(inserted_speed_mps=5.1)
    socket_server = FakeSocketServer()
    client = make_client_with_socket(session, socket_server)
    payload = valid_payload() | {"speed_mps": 5.1}

    response = client.post("/api/telemetry", json=payload)

    assert response.status_code == 201
    assert socket_server.emitted[1][0] == "anomaly:detected"
    assert socket_server.emitted[1][1]["reasons"] == ["overspeed"]


def test_create_telemetry_event_does_not_broadcast_normal_anomaly() -> None:
    session = FakeSession()
    socket_server = FakeSocketServer()
    client = make_client_with_socket(session, socket_server)

    response = client.post("/api/telemetry", json=valid_payload())

    assert response.status_code == 201
    assert [event for event, _data in socket_server.emitted] == ["telemetry:created"]


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


def test_create_telemetry_event_rejects_timestamp_without_z() -> None:
    client = make_client(FakeSession())
    payload = valid_payload() | {"timestamp": "2026-05-28T12:00:00.740"}

    response = client.post("/api/telemetry", json=payload)

    assert response.status_code == 422


def test_create_telemetry_event_rejects_offset_timestamp() -> None:
    client = make_client(FakeSession())
    payload = valid_payload() | {"timestamp": "2026-05-28T12:00:00.740+00:00"}

    response = client.post("/api/telemetry", json=payload)

    assert response.status_code == 422


def test_create_telemetry_event_returns_bad_request_for_invalid_vehicle() -> None:
    session = FakeSession(fail_commit=True)
    client = make_client(session)

    response = client.post("/api/telemetry", json=valid_payload())

    assert response.status_code == 400
    assert response.json() == {"detail": "Invalid vehicle_id"}


def test_socketio_app_uses_dashboard_path() -> None:
    fastapi_app = create_app(enable_lifespan=False)
    app = create_asgi_app(fastapi_app, fastapi_app.state.settings)

    assert app.engineio_path == "/dashboard.io/"
