from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from backend.app.schemas.types import TelemetryStatus, ZoneEntered


class TelemetryEventBase(BaseModel):
    vehicle_id: str
    timestamp: datetime
    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)
    battery_pct: float = Field(ge=0, le=100)
    speed_mps: float = Field(ge=0)
    status: TelemetryStatus
    error_codes: list[str]
    zone_entered: ZoneEntered | None = None


class TelemetryEventCreate(TelemetryEventBase):
    pass


class TelemetryEventRead(TelemetryEventBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    received_at: datetime
