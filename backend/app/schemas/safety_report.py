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
    activity: Optional[str] = Field(default=None, description="Inferred or declared operational activity")
    activity_category: Optional[str] = Field(default=None, description="Operational activity group")
    site: Optional[str] = Field(default=None, description="Specific rig, plant unit, or facility site")
    field: Optional[str] = Field(default=None, description="Oil field or basin")
    installation: Optional[str] = Field(default=None, description="Installation or asset name")
    actual_consequence: Optional[str] = Field(default="No injury", description="Observed consequence outcome")
    potential_consequence: Optional[str] = Field(default=None, description="Worst-case credible outcome")
    fatality_potential: Optional[bool] = Field(default=False, description="Flag indicating potential for fatality")
    life_saving_rule: Optional[str] = Field(default=None, description="Associated IOGP Life-Saving Rule")
    failed_barrier: Optional[str] = Field(default=None, description="Ground-truth failed barrier label")
    is_sif: Optional[bool] = Field(default=None, description="Ground-truth SIF label for evaluation")


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
    activity: Optional[str] = None
    activity_category: Optional[str] = None
    site: Optional[str] = None
    field: Optional[str] = None
    installation: Optional[str] = None
    actual_consequence: Optional[str] = None
    potential_consequence: Optional[str] = None
    fatality_potential: Optional[bool] = None
    life_saving_rule: Optional[str] = None
    failed_barrier: Optional[str] = None
    is_sif: Optional[bool] = None


class SafetyReportResponse(SafetyReportBase):
    id: int
    case_id: str
    created_by: Optional[int] = None
    processing_status: ProcessingStatus
    source_type: Optional[str] = "MANUAL"
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
