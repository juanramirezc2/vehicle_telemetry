import re
from datetime import datetime, timezone

from pydantic import BaseModel, ConfigDict, Field, field_validator

from backend.app.schemas.types import TelemetryStatus, ZoneEntered

UTC_TIMESTAMP_PATTERN = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?Z$"
)


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
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "vehicle_id": "vehicle-1",
                "timestamp": "2026-05-28T22:19:15.740Z",
                "lat": 37.41,
                "lon": -122.08,
                "battery_pct": 78,
                "speed_mps": 1.2,
                "status": "moving",
                "error_codes": [],
                "zone_entered": None,
            }
        }
    )

    @field_validator("timestamp", mode="before")
    @classmethod
    def parse_utc_timestamp(cls, value: str) -> datetime:
        if not isinstance(value, str) or not UTC_TIMESTAMP_PATTERN.fullmatch(value):
            raise ValueError("timestamp must be a UTC date-time string ending in Z")

        timestamp = datetime.fromisoformat(f"{value[:-1]}+00:00")
        return timestamp.astimezone(timezone.utc).replace(tzinfo=None)


class TelemetryEventRead(TelemetryEventBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    received_at: datetime
