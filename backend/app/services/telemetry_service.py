from sqlalchemy import insert, update, func
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models import TelemetryEvent, ZoneCounter
from backend.app.schemas.telemetry import TelemetryEventCreate, TelemetryEventRead


class InvalidVehicleError(Exception):
    """Raised when a telemetry event references a vehicle_id that doesn't exist."""


async def ingest_telemetry(
    session: AsyncSession,
    event: TelemetryEventCreate,
) -> TelemetryEventRead:
    """
    Persist a telemetry event and, if it represents a zone crossing,
    atomically increment the corresponding zone counter.

    Both writes happen inside a single transaction: either both commit
    or neither does. The zone counter increment uses a server-side
    expression (`entry_count = entry_count + 1`) which Postgres executes
    atomically under a row-level lock, so concurrent crossings of the
    same zone serialize correctly without losing entries.
    """
    async with session.begin():
        # 1. Insert the telemetry event, get the stored row back.
        result = await session.execute(
            insert(TelemetryEvent)
            .values(**event.model_dump())
            .returning(TelemetryEvent)
        )
        stored = result.scalar_one()

        # zone crossing
        if event.zone_entered is not None:
            await session.execute(
                update(ZoneCounter)
                .where(ZoneCounter.zone_id == event.zone_entered)
                .values(
                    entry_count=ZoneCounter.entry_count + 1,
                    updated_at=func.now(),
                )
            )

    return TelemetryEventRead.model_validate(stored)
