from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field
from app.models.enums import IncidentType, ProcessingStatus
from app.schemas.department import DepartmentResponse
from app.schemas.location import LocationResponse
from app.schemas.user import UserResponse


class SafetyReportBase(BaseModel):
    job_role: str = Field(..., min_length=2, max_length=100, description="Job role or title of worker/observer")
    department_id: int = Field(..., description="ID of the department where incident occurred")
    location_id: int = Field(..., description="ID of the specific plant unit/location")
    task: str = Field(..., min_length=2, max_length=255, description="Work task being executed at time of observation")
    incident_type: IncidentType = Field(..., description="Classification category")
    description: str = Field(
        ...,
        min_length=10,
        max_length=3000,
        description="Factual, unedited description of what occurred",
    )
    reported_at: Optional[datetime] = Field(default=None, description="Datetime when event occurred")


class SafetyReportCreate(SafetyReportBase):
    case_id: Optional[str] = Field(default=None, max_length=50, description="Optional custom Case ID")


class SafetyReportUpdate(BaseModel):
    job_role: Optional[str] = Field(default=None, min_length=2, max_length=100)
    department_id: Optional[int] = None
    location_id: Optional[int] = None
    task: Optional[str] = Field(default=None, min_length=2, max_length=255)
    incident_type: Optional[IncidentType] = None
    description: Optional[str] = Field(default=None, min_length=10, max_length=3000)
    processing_status: Optional[ProcessingStatus] = None


class SafetyReportResponse(SafetyReportBase):
    id: int
    case_id: str
    created_by: Optional[int] = None
    processing_status: ProcessingStatus
    created_at: datetime
    updated_at: datetime
    department: Optional[DepartmentResponse] = None
    location: Optional[LocationResponse] = None
    reporter: Optional[UserResponse] = None

    model_config = ConfigDict(from_attributes=True)


class PaginatedSafetyReportResponse(BaseModel):
    items: List[SafetyReportResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
