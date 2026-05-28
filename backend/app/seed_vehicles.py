from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any, get_args

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import create_async_engine

from backend.app.core.config import get_settings
from backend.app.models import Vehicle
from backend.app.schemas.types import TelemetryStatus, ZoneEntered

VEHICLE_COUNT = 50
VEHICLE_STATUSES = get_args(TelemetryStatus)
VEHICLE_ZONES = get_args(ZoneEntered)


def build_seed_vehicles(*, updated_at: datetime | None = None) -> list[dict[str, Any]]:
    timestamp = updated_at or datetime.now(timezone.utc).replace(tzinfo=None)

    return [
        {
            "id": f"v-{index}",
            "status": VEHICLE_STATUSES[(index - 1) % len(VEHICLE_STATUSES)],
            "battery": float(50 + ((index - 1) * 7) % 51),
            "current_zone": None
            if index % 10 == 0
            else VEHICLE_ZONES[(index - 1) % len(VEHICLE_ZONES)],
            "updated_at": timestamp,
        }
        for index in range(1, VEHICLE_COUNT + 1)
    ]


async def seed_vehicles() -> int:
    engine = create_async_engine(get_settings().database_url)
    vehicles = build_seed_vehicles()
    statement = insert(Vehicle).values(vehicles)
    update_statement = statement.on_conflict_do_update(
        index_elements=[Vehicle.id],
        set_={
            "status": statement.excluded.status,
            "battery": statement.excluded.battery,
            "current_zone": statement.excluded.current_zone,
            "updated_at": statement.excluded.updated_at,
        },
    )

    try:
        async with engine.begin() as connection:
            await connection.execute(update_statement)
    finally:
        await engine.dispose()

    return len(vehicles)


def main() -> None:
    count = asyncio.run(seed_vehicles())
    print(f"Seeded {count} vehicles.")


if __name__ == "__main__":
    main()
