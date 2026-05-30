from datetime import datetime

from pydantic import BaseModel, ConfigDict


class MissionBase(BaseModel):
    vehicle_id: str
    status: str
    started_at: datetime | None = None
    cancelled_at: datetime | None = None
    cancel_reason: str | None = None


class MissionCreate(MissionBase):
    id: str


class MissionRead(MissionBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
