from uuid import uuid4

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models import MaintenanceRecord, Mission, Vehicle


class VehicleNotFoundError(Exception):
    """Raised when a vehicle with the given ID cannot be found."""

    def __init__(self, vehicle_id: str):
        self.vehicle_id = vehicle_id
        super().__init__(f"Vehicle with ID {vehicle_id} not found")


async def apply_status_change(
    session: AsyncSession,
    vehicle_id: str,
    new_status: str,
    reason: str | None = None,
    triggering_event_id: str | None = None,
) -> Vehicle | None:
    """
    Lock the vehicle, transition its status, run fault-specific side effects.
    No-op (returns None) if vehicle is already in the target status.
    MUST be called inside an existing transaction — caller owns the boundary.
    """
    result = await session.execute(
        select(Vehicle).where(Vehicle.id == vehicle_id).with_for_update()
    )
    vehicle = result.scalar_one_or_none()
    if vehicle is None:
        raise VehicleNotFoundError(vehicle_id)

    if vehicle.status == new_status:
        return None  # idempotent no-op

    previous = vehicle.status
    vehicle.status = new_status

    if new_status == "fault":
        await session.execute(
            update(Mission)
            .where(Mission.vehicle_id == vehicle_id, Mission.status == "active")
            .values(
                status="cancelled",
                cancelled_at=func.now(),
                cancel_reason=reason or f"fault transition from {previous}",
            )
        )
        session.add(
            MaintenanceRecord(
                id=str(uuid4()),
                vehicle_id=vehicle_id,
                reason=reason or f"auto-opened on fault from {previous}",
                triggering_event_id=triggering_event_id,
            )
        )

    return vehicle
