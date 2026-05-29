from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ZoneCountRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    zone_id: str
    entry_count: int = Field(ge=0)
    updated_at: datetime | None
