from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class VehicleBase(BaseModel):
    status: str = Field(max_length=16)
    battery: float
    current_zone: str | None = None
    updated_at: datetime


class VehicleCreate(VehicleBase):
    id: str


class VehicleRead(VehicleBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
