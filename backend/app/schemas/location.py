from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class LocationBase(BaseModel):
    name: str
    description: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class LocationCreate(LocationBase):
    pass


class LocationUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class LocationResponse(LocationBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
