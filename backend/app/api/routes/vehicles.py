from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.database import get_session
from backend.app.models import Vehicle
from backend.app.schemas import VehicleRead

router = APIRouter(tags=["vehicles"])


@router.get("/vehicles", response_model=list[VehicleRead])
async def list_vehicles(
    limit: int = Query(default=500, ge=1, le=5000),
    session: AsyncSession = Depends(get_session),
) -> list[Vehicle]:
    result = await session.execute(select(Vehicle).order_by(Vehicle.id).limit(limit))
    return list(result.scalars())
