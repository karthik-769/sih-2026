from typing import List, Optional, Dict, Any
from pydantic import BaseModel


class DashboardKpis(BaseModel):
    total_reports: int
    critical_risk_count: int
    high_risk_count: int
    sif_precursors_count: int
    active_alerts_count: int
    open_actions_count: int
    overdue_actions_count: int
    total_batches_count: int


class TrendPoint(BaseModel):
    period: str  # e.g., '2026-W35' or '2026-09-01'
    label: str
    value: float
    count: int = 0
    sif_count: int = 0


class HazardTrendItem(BaseModel):
    hazard: str
    count: int
    percentage: float
    sif_count: int


class DepartmentRiskItem(BaseModel):
    department_id: int
    department_name: str
    total_reports: int
    avg_risk_score: float
    sif_count: int
    critical_count: int
    risk_level: str


class LocationRiskItem(BaseModel):
    location_id: int
    location_name: str
    total_reports: int
    avg_risk_score: float
    sif_count: int
    critical_count: int
    open_actions_count: int
    risk_level: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    main_hazard: Optional[str] = None


class TopRiskAreaItem(BaseModel):
    rank: int
    location_id: int
    location_name: str
    risk_level: str
    risk_score: float
    main_hazard: str
    sif_count: int
    total_reports: int
    open_actions: int


class RiskMapMarker(BaseModel):
    location_id: int
    location_name: str
    latitude: float
    longitude: float
    risk_score: float
    risk_level: str
    total_reports: int
    high_risk_reports: int
    sif_precursors: int
    top_hazards: List[str] = []
    open_corrective_actions: int
    recent_alerts: List[str] = []
