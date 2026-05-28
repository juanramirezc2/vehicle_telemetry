from datetime import datetime

import pytest
from pydantic import ValidationError

from backend.app.models import TelemetryEvent
from backend.app.schemas import TelemetryEventCreate, TelemetryEventRead


def valid_telemetry_payload() -> dict[str, object]:
    return {
        "vehicle_id": "vehicle-1",
        "timestamp": "2026-05-28T12:00:00.740Z",
        "lat": 37.7749,
        "lon": -122.4194,
        "battery_pct": 86.5,
        "speed_mps": 1.2,
        "status": "moving",
        "error_codes": [],
        "zone_entered": "aisle_a",
    }


def test_telemetry_create_validates_valid_payload() -> None:
    telemetry = TelemetryEventCreate.model_validate(valid_telemetry_payload())

    assert telemetry.vehicle_id == "vehicle-1"
    assert telemetry.timestamp == datetime(2026, 5, 28, 12, 0, 0, 740000)
    assert telemetry.timestamp.tzinfo is None
    assert telemetry.zone_entered == "aisle_a"


def test_telemetry_create_allows_empty_zone_entered() -> None:
    payload = valid_telemetry_payload() | {"zone_entered": None}

    telemetry = TelemetryEventCreate.model_validate(payload)

    assert telemetry.zone_entered is None


def test_telemetry_create_accepts_utc_timestamp_without_fractional_seconds() -> None:
    payload = valid_telemetry_payload() | {"timestamp": "2026-05-28T12:00:00Z"}

    telemetry = TelemetryEventCreate.model_validate(payload)

    assert telemetry.timestamp == datetime(2026, 5, 28, 12, 0, 0)


@pytest.mark.parametrize(
    "timestamp",
    [
        "2026-05-28T12:00:00.740",
        "2026-05-28T12:00:00.740+00:00",
        "2026-05-28T07:00:00.740-05:00",
        "2026-05-28t12:00:00.740z",
        datetime(2026, 5, 28, 12, 0, 0),
    ],
)
def test_telemetry_create_rejects_non_utc_z_timestamp(timestamp: object) -> None:
    payload = valid_telemetry_payload() | {"timestamp": timestamp}

    with pytest.raises(ValidationError):
        TelemetryEventCreate.model_validate(payload)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("battery_pct", -1),
        ("battery_pct", 101),
        ("speed_mps", -0.1),
        ("status", "offline"),
        ("zone_entered", "unknown_zone"),
        ("lat", -91),
        ("lat", 91),
        ("lon", -181),
        ("lon", 181),
    ],
)
def test_telemetry_create_rejects_invalid_values(
    field: str, value: object
) -> None:
    payload = valid_telemetry_payload() | {field: value}

    with pytest.raises(ValidationError):
        TelemetryEventCreate.model_validate(payload)


def test_telemetry_read_serializes_orm_instance() -> None:
    received_at = datetime(2026, 5, 28, 12, 0, 1)
    telemetry = TelemetryEvent(
        id="event-1",
        vehicle_id="vehicle-1",
        timestamp=datetime(2026, 5, 28, 12, 0, 0),
        received_at=received_at,
        lat=37.7749,
        lon=-122.4194,
        battery_pct=86.5,
        speed_mps=1.2,
        status="moving",
        error_codes=[],
        zone_entered="aisle_a",
    )

    schema = TelemetryEventRead.model_validate(telemetry)

    assert schema.id == "event-1"
    assert schema.received_at == received_at
