from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class PatternResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    pattern_key: str
    title: str
    pattern_type: str
    hazard_category: Optional[str] = None
    sif_category: Optional[str] = None
    department_id: Optional[int] = None
    department_name: Optional[str] = None
    location_id: Optional[int] = None
    location_name: Optional[str] = None
    risk_score: float
    risk_level: str
    frequency_count: int
    sif_count: int
    trend_percentage: float
    scoring_factors: Dict[str, Any] = {}
    evidence_report_ids: List[int] = []
    evidence_case_ids: List[str] = []
    recommendations: List[str] = []
    status: str
    first_detected_at: datetime
    last_detected_at: datetime
    created_at: datetime
    updated_at: datetime


class PaginatedPatternResponse(BaseModel):
    items: List[PatternResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
