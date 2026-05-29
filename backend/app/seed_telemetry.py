from __future__ import annotations

import asyncio
import random
from datetime import datetime, timedelta, timezone
from typing import Any, get_args
from uuid import uuid4

from sqlalchemy import insert, select
from sqlalchemy.ext.asyncio import create_async_engine

from backend.app.core.config import get_settings
from backend.app.models import TelemetryEvent, Vehicle
from backend.app.schemas.types import TelemetryStatus, ZoneEntered

TELEMETRY_COUNT = 100
STATUSES = list(get_args(TelemetryStatus))
ZONES = list(get_args(ZoneEntered))
ERROR_CODES = [
    "E_BATTERY_LOW",
    "E_MOTOR_OVERHEAT",
    "E_SENSOR_FAULT",
    "E_NAV_LOST",
    "E_COMMS_TIMEOUT",
]


def build_seed_telemetry(
    vehicle_ids: list[str],
    *,
    count: int = TELEMETRY_COUNT,
    now: datetime | None = None,
    rng: random.Random | None = None,
) -> list[dict[str, Any]]:
    if not vehicle_ids:
        raise ValueError("vehicle_ids must not be empty; seed vehicles first")

    generator = rng or random.Random()
    reference = now or datetime.now(timezone.utc).replace(tzinfo=None)

    events: list[dict[str, Any]] = []
    for _ in range(count):
        status = generator.choice(STATUSES)
        events.append(
            {
                "id": str(uuid4()),
                "vehicle_id": generator.choice(vehicle_ids),
                "timestamp": reference
                - timedelta(seconds=generator.randint(0, 24 * 60 * 60)),
                "lat": round(generator.uniform(-90, 90), 6),
                "lon": round(generator.uniform(-180, 180), 6),
                "battery_pct": round(generator.uniform(0, 100), 1),
                "speed_mps": round(generator.uniform(0.1, 3.5), 2)
                if status == "moving"
                else 0.0,
                "status": status,
                "error_codes": generator.sample(ERROR_CODES, generator.randint(1, 2))
                if status == "fault"
                else [],
                "zone_entered": generator.choice(ZONES)
                if generator.random() < 0.2
                else None,
            }
        )

    return events


async def seed_telemetry(count: int = TELEMETRY_COUNT) -> int:
    engine = create_async_engine(get_settings().database_url)

    try:
        async with engine.begin() as connection:
            result = await connection.execute(select(Vehicle.id))
            vehicle_ids = [row[0] for row in result]

            events = build_seed_telemetry(vehicle_ids, count=count)
            await connection.execute(insert(TelemetryEvent), events)
    finally:
        await engine.dispose()

    return len(events)


def main() -> None:
    count = asyncio.run(seed_telemetry())
    print(f"Seeded {count} telemetry events.")


if __name__ == "__main__":
    main()
