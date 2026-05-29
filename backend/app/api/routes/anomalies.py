from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.database import get_session
from backend.app.schemas.anomaly import AnomalyRead, anomaly_from_telemetry
from backend.app.schemas.telemetry import parse_utc_timestamp
from backend.app.services.anomaly_service import (
    detect_anomaly_reasons,
    get_recent_anomalies,
)

router = APIRouter(tags=["anomalies"])


def parse_query_timestamp(value: str | None, field_name: str) -> datetime | None:
    if value is None:
        return None

    try:
        return parse_utc_timestamp(value)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=f"{field_name} must be a UTC date-time string ending in Z",
        ) from exc


@router.get("/anomalies", response_model=list[AnomalyRead])
async def list_anomalies(
    vehicle_id: str | None = None,
    start: str | None = None,
    end: str | None = None,
    limit: int = Query(default=500, ge=1, le=5000),
    session: AsyncSession = Depends(get_session),
) -> list[AnomalyRead]:
    start_dt = parse_query_timestamp(start, "start")
    end_dt = parse_query_timestamp(end, "end")
    distinct_vehicle = vehicle_id is None and start_dt is None and end_dt is None

    events = await get_recent_anomalies(
        session,
        vehicle_id=vehicle_id,
        start=start_dt,
        end=end_dt,
        limit=limit,
        distinct_vehicle=distinct_vehicle,
    )
    return [
        anomaly_from_telemetry(event, detect_anomaly_reasons(event))
        for event in events
    ]
