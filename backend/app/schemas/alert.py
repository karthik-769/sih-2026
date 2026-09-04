from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class AlertResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    alert_key: str
    pattern_id: Optional[int] = None
    alert_type: str
    title: str
    description: str
    severity: str
    risk_score: float
    department_id: Optional[int] = None
    department_name: Optional[str] = None
    location_id: Optional[int] = None
    location_name: Optional[str] = None
    hazard_category: Optional[str] = None
    sif_category: Optional[str] = None
    explanation_evidence: List[str] = []
    contributing_report_ids: List[int] = []
    contributing_case_ids: List[str] = []
    recommended_actions: List[str] = []
    status: str
    acknowledged_at: Optional[datetime] = None
    acknowledged_by: Optional[int] = None
    acknowledged_by_name: Optional[str] = None
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[int] = None
    resolved_by_name: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class AlertUpdate(BaseModel):
    status: Optional[str] = Field(None, description="NEW, ACKNOWLEDGED, IN_PROGRESS, RESOLVED, DISMISSED")
    notes: Optional[str] = None


class PaginatedAlertResponse(BaseModel):
    items: List[AlertResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
