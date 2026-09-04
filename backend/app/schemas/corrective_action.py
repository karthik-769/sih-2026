from typing import Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class CorrectiveActionCreate(BaseModel):
    alert_id: Optional[int] = None
    pattern_id: Optional[int] = None
    report_id: Optional[int] = None
    title: str = Field(..., min_length=3, max_length=255)
    description: str = Field(..., min_length=5)
    recommended_action: str = Field(..., min_length=3)
    assigned_to: Optional[int] = None
    department_id: Optional[int] = None
    location_id: Optional[int] = None
    priority: str = Field(default="MEDIUM", description="LOW, MEDIUM, HIGH, CRITICAL")
    due_date: Optional[datetime] = None


class CorrectiveActionUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    recommended_action: Optional[str] = None
    assigned_to: Optional[int] = None
    department_id: Optional[int] = None
    location_id: Optional[int] = None
    priority: Optional[str] = None
    due_date: Optional[datetime] = None
    status: Optional[str] = Field(None, description="OPEN, ASSIGNED, IN_PROGRESS, RESOLVED, OVERDUE, CANCELLED")
    resolution_notes: Optional[str] = None


class CorrectiveActionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    action_number: str
    alert_id: Optional[int] = None
    pattern_id: Optional[int] = None
    report_id: Optional[int] = None
    title: str
    description: str
    recommended_action: str
    assigned_to: Optional[int] = None
    assignee_name: Optional[str] = None
    assignee_email: Optional[str] = None
    department_id: Optional[int] = None
    department_name: Optional[str] = None
    location_id: Optional[int] = None
    location_name: Optional[str] = None
    priority: str
    due_date: Optional[datetime] = None
    status: str
    is_overdue: bool = False
    resolution_notes: Optional[str] = None
    created_by: Optional[int] = None
    creator_name: Optional[str] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class PaginatedCorrectiveActionResponse(BaseModel):
    items: list[CorrectiveActionResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
