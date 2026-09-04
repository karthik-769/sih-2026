from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class DepartmentBase(BaseModel):
    name: str
    description: Optional[str] = None


class DepartmentCreate(DepartmentBase):
    pass


class DepartmentUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class DepartmentResponse(DepartmentBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DepartmentStats(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    created_at: datetime
    total_reports: int
    high_risk_reports: int
    critical_risk_reports: int
    sif_precursors: int
    active_alerts: int
    open_actions: int
