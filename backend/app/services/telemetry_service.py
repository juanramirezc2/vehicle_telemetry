from typing import NamedTuple
from uuid import uuid4

from sqlalchemy import func, insert, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models import TelemetryEvent, Vehicle, ZoneCounter
from backend.app.schemas.telemetry import TelemetryEventCreate, TelemetryEventRead
from backend.app.services.vehicle_service import (
    VehicleNotFoundError,
    apply_status_change,
)


class InvalidVehicleError(Exception):
    """Raised when a telemetry event references a vehicle_id that doesn't exist."""


class TelemetryIngestResult(NamedTuple):
    telemetry: TelemetryEventRead
    changed_vehicle: Vehicle | None


async def ingest_telemetry(
    session: AsyncSession,
    event: TelemetryEventCreate,
) -> TelemetryIngestResult:
    """
    Persist a telemetry event and, if it represents a zone crossing,
    atomically increment the corresponding zone counter.

    Both writes happen inside a single transaction: either both commit
    or neither does. The zone counter increment uses a server-side
    expression (`entry_count = entry_count + 1`) which Postgres executes
    atomically under a row-level lock, so concurrent crossings of the
    same zone serialize correctly without losing entries.
    """
    changed_vehicle: Vehicle | None = None
    telemetry_id = str(uuid4())

    try:
        async with session.begin():
            if event.status == "fault":
                result = await session.execute(
                    select(Vehicle.id)
                    .where(Vehicle.id == event.vehicle_id)
                    .with_for_update()
                )
                if result.scalar_one_or_none() is None:
                    raise InvalidVehicleError

            # 1. Insert the telemetry event, get the stored row back.
            result = await session.execute(
                insert(TelemetryEvent)
                .values(id=telemetry_id, **event.model_dump())
                .returning(TelemetryEvent)
            )
            stored = result.scalar_one()

            if event.status == "fault":
                changed_vehicle = await apply_status_change(
                    session,
                    event.vehicle_id,
                    "fault",
                    reason="fault telemetry event",
                    triggering_event_id=stored.id,
                )

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
    except (IntegrityError, VehicleNotFoundError) as exc:
        raise InvalidVehicleError from exc

    return TelemetryIngestResult(
        telemetry=TelemetryEventRead.model_validate(stored),
        changed_vehicle=changed_vehicle,
    )
