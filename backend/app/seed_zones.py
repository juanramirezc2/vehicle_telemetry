from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any, get_args

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import create_async_engine

from backend.app.core.config import get_settings
from backend.app.models import ZoneCounter
from backend.app.schemas.types import ZoneEntered

ZONES = list(get_args(ZoneEntered))


def build_seed_zones(*, updated_at: datetime | None = None) -> list[dict[str, Any]]:
    timestamp = updated_at or datetime.now(timezone.utc).replace(tzinfo=None)

    return [
        {
            "zone_id": zone,
            "entry_count": 0,
            "updated_at": timestamp,
        }
        for zone in ZONES
    ]


async def seed_zones() -> int:
    engine = create_async_engine(get_settings().database_url)
    zones = build_seed_zones()
    statement = insert(ZoneCounter).values(zones)
    update_statement = statement.on_conflict_do_update(
        index_elements=[ZoneCounter.zone_id],
        set_={
            "updated_at": statement.excluded.updated_at,
        },
    )

    try:
        async with engine.begin() as connection:
            await connection.execute(update_statement)
    finally:
        await engine.dispose()

    return len(zones)


def main() -> None:
    count = asyncio.run(seed_zones())
    print(f"Seeded {count} zones.")


if __name__ == "__main__":
    main()
