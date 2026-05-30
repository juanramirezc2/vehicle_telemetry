from __future__ import annotations

import asyncio
import random
from datetime import datetime, timedelta, timezone
from typing import Any, get_args

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import create_async_engine

from backend.app.core.config import get_settings
from backend.app.models import ZoneCounter
from backend.app.schemas.types import ZoneEntered

ZONES = list(get_args(ZoneEntered))


def build_seed_zones(
    *,
    now: datetime | None = None,
    rng: random.Random | None = None,
) -> list[dict[str, Any]]:
    generator = rng or random.Random()
    reference = now or datetime.now(timezone.utc).replace(tzinfo=None)

    return [
        {
            "zone_id": zone,
            "entry_count": generator.randint(0, 500),
            "updated_at": reference
            - timedelta(seconds=generator.randint(0, 24 * 60 * 60)),
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
            "entry_count": statement.excluded.entry_count,
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
