from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models import ZoneCounter


async def get_all_zone_counts(session: AsyncSession) -> list[ZoneCounter]:
    result = await session.execute(select(ZoneCounter).order_by(ZoneCounter.zone_id))
    return list(result.scalars().all())
