from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.database import get_session
from backend.app.models import TelemetryEvent
from backend.app.schemas import TelemetryEventCreate, TelemetryEventRead
from backend.app.services.anomaly_service import detect_anomaly_reasons
from backend.app.services.telemetry_service import InvalidVehicleError, ingest_telemetry

router = APIRouter(tags=["telemetry"])


@router.get("/telemetry", response_model=list[TelemetryEventRead])
async def list_telemetry_events(
    limit: int = Query(default=500, ge=1, le=5000),
    session: AsyncSession = Depends(get_session),
) -> list[TelemetryEvent]:
    result = await session.execute(
        select(TelemetryEvent).order_by(TelemetryEvent.timestamp.desc()).limit(limit)
    )
    return list(result.scalars())


@router.get("/events", response_model=list[TelemetryEventRead])
async def list_latest_events_by_vehicle(
    session: AsyncSession = Depends(get_session),
) -> list[TelemetryEvent]:
    result = await session.execute(
        select(TelemetryEvent)
        .distinct(TelemetryEvent.vehicle_id)
        .order_by(TelemetryEvent.vehicle_id, TelemetryEvent.timestamp.desc())
    )
    return list(result.scalars())


@router.post(
    "/telemetry", response_model=TelemetryEventRead, status_code=status.HTTP_201_CREATED
)
async def create_telemetry_event(
    payload: TelemetryEventCreate,
    request: Request,
    session: AsyncSession = Depends(get_session),
) -> TelemetryEventRead:
    try:
        telemetry = await ingest_telemetry(session, payload)
    except InvalidVehicleError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid vehicle_id",
        ) from exc

    response = TelemetryEventRead.model_validate(telemetry)

    socketio_server = getattr(request.app.state, "socketio", None)
    if socketio_server is not None:
        telemetry_payload = response.model_dump(mode="json")
        await socketio_server.emit("telemetry:created", telemetry_payload)
        if payload.zone_entered is not None:
            await socketio_server.emit(
                "zones:count_changed",
                {"zone_id": payload.zone_entered},
            )
        reasons = detect_anomaly_reasons(response)
        if reasons:
            await socketio_server.emit(
                "anomaly:detected",
                telemetry_payload | {"reasons": reasons},
            )

    return response
