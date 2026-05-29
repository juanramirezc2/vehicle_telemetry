import random
from datetime import datetime

import pytest

from backend.app.schemas import TelemetryEventRead
from backend.app.seed_telemetry import (
    STATUSES,
    TELEMETRY_COUNT,
    ZONES,
    build_seed_telemetry,
)

VEHICLE_IDS = [f"v-{index}" for index in range(1, 51)]


def test_build_seed_telemetry_generates_requested_count() -> None:
    events = build_seed_telemetry(VEHICLE_IDS, rng=random.Random(1))

    assert len(events) == TELEMETRY_COUNT


def test_build_seed_telemetry_requires_vehicle_ids() -> None:
    with pytest.raises(ValueError):
        build_seed_telemetry([])


def test_build_seed_telemetry_produces_valid_rows() -> None:
    now = datetime(2026, 5, 28, 12, 0, 0)
    events = build_seed_telemetry(VEHICLE_IDS, now=now, rng=random.Random(7))

    for event in events:
        assert event["vehicle_id"] in VEHICLE_IDS
        assert event["status"] in STATUSES
        assert -90 <= event["lat"] <= 90
        assert -180 <= event["lon"] <= 180
        assert 0 <= event["battery_pct"] <= 100
        assert event["speed_mps"] >= 0
        assert event["zone_entered"] is None or event["zone_entered"] in ZONES
        assert event["timestamp"] <= now

        # Every row must satisfy the API/DB validation contract.
        TelemetryEventRead.model_validate(
            {**event, "received_at": now},
            from_attributes=False,
        )
