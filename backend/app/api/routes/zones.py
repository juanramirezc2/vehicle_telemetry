from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.database import get_session
from backend.app.schemas.zone import ZoneCountRead
from backend.app.services.zone_service import get_all_zone_counts

router = APIRouter(prefix="/zones", tags=["zones"])


@router.get("/counts", response_model=list[ZoneCountRead])
async def list_zone_counts(session: AsyncSession = Depends(get_session)):
    return await get_all_zone_counts(session)
