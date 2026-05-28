from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.database import get_session
from backend.app.models import TelemetryEvent
from backend.app.schemas import TelemetryEventCreate, TelemetryEventRead

router = APIRouter(tags=["telemetry"])


@router.post(
    "/telemetry",
    response_model=TelemetryEventRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_telemetry_event(
    payload: TelemetryEventCreate,
    session: AsyncSession = Depends(get_session),
) -> TelemetryEvent:
    telemetry = TelemetryEvent(
        id=str(uuid4()),
        **payload.model_dump(),
    )

    session.add(telemetry)

    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid vehicle_id",
        ) from exc

    await session.refresh(telemetry)
    return telemetry
