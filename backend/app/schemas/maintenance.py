from datetime import datetime

from pydantic import BaseModel, ConfigDict


class MaintenanceRecordBase(BaseModel):
    vehicle_id: str
    reason: str
    triggering_event_id: str | None = None


class MaintenanceRecordCreate(MaintenanceRecordBase):
    id: str


class MaintenanceRecordRead(MaintenanceRecordBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    opened_at: datetime
