from pydantic import BaseModel, ConfigDict


class MissionBase(BaseModel):
    vehicle_id: str
    status: str


class MissionCreate(MissionBase):
    id: str


class MissionRead(MissionBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
