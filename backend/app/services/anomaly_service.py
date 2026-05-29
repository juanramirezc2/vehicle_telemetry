from datetime import datetime

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models import TelemetryEvent

LOW_BATTERY_PCT = 5
MAX_SPEED_MPS = 5


def detect_anomaly_reasons(event: object) -> list[str]:
    reasons: list[str] = []

    if getattr(event, "battery_pct") < LOW_BATTERY_PCT:
        reasons.append("low_battery")
    if getattr(event, "speed_mps") > MAX_SPEED_MPS:
        reasons.append("overspeed")

    return reasons


async def get_recent_anomalies(
    session: AsyncSession,
    *,
    vehicle_id: str | None = None,
    start: datetime | None = None,
    end: datetime | None = None,
    limit: int = 500,
) -> list[TelemetryEvent]:
    statement = select(TelemetryEvent).where(
        or_(
            TelemetryEvent.battery_pct < LOW_BATTERY_PCT,
            TelemetryEvent.speed_mps > MAX_SPEED_MPS,
        )
    )

    if vehicle_id is not None:
        statement = statement.where(TelemetryEvent.vehicle_id == vehicle_id)
    if start is not None:
        statement = statement.where(TelemetryEvent.timestamp >= start)
    if end is not None:
        statement = statement.where(TelemetryEvent.timestamp <= end)

    result = await session.execute(
        statement.order_by(TelemetryEvent.timestamp.desc()).limit(limit)
    )
    return list(result.scalars())
