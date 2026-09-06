from typing import List, Optional, Dict, Any
from pydantic import BaseModel


class DashboardKpis(BaseModel):
    total_reports: int
    critical_risk_count: int
    high_risk_count: int
    sif_precursors_count: int
    sif_density: float = 0.0
    active_alerts_count: int
    emerging_risks_count: int = 0
    open_actions_count: int
    overdue_actions_count: int
    total_batches_count: int


class TrendPoint(BaseModel):
    period: str  # e.g., '2026-W35' or '2026-09-01'
    label: str
    value: float
    count: int = 0
    sif_count: int = 0
    sif_density: float = 0.0


class HazardTrendItem(BaseModel):
    hazard: str
    count: int
    percentage: float
    sif_count: int
    sif_density: float = 0.0


class DepartmentRiskItem(BaseModel):
    department_id: int
    department_name: str
    total_reports: int
    avg_risk_score: float
    sif_count: int
    sif_density: float = 0.0
    trend_percentage: float = 0.0
    critical_count: int
    risk_level: str


class LocationRiskItem(BaseModel):
    location_id: int
    location_name: str
    total_reports: int
    avg_risk_score: float
    sif_count: int
    sif_density: float = 0.0
    trend_percentage: float = 0.0
    critical_count: int
    open_actions_count: int
    risk_level: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    main_hazard: Optional[str] = None
    top_barrier_failure: Optional[str] = None


class ActivityRiskItem(BaseModel):
    activity: str
    activity_category: Optional[str] = "General Operations"
    total_reports: int
    sif_count: int
    sif_density: float = 0.0
    avg_risk_score: float = 0.0
    top_hazard: Optional[str] = None
    top_barrier_failure: Optional[str] = None
    trend_percentage: float = 0.0


class LifeSavingRuleRiskItem(BaseModel):
    rule_name: str
    total_reports: int
    sif_count: int
    sif_density: float = 0.0
    avg_risk_score: float = 0.0
    trend_percentage: float = 0.0
    top_hazards: List[str] = []
    top_barrier_failures: List[str] = []
    top_locations: List[str] = []
    top_activities: List[str] = []


class BarrierFailureRecurrenceItem(BaseModel):
    barrier_name: str
    hierarchy_level: str = "ENGINEERING"
    total_reports: int
    sif_count: int
    sif_density: float = 0.0
    trend_percentage: float = 0.0
    affected_activities: List[str] = []
    affected_locations: List[str] = []


class TrendComparisonResponse(BaseModel):
    window_days: int
    current_period_reports: int
    previous_period_reports: int
    frequency_change_pct: float
    current_sif_count: int
    previous_sif_count: int
    sif_count_change_pct: float
    current_sif_density: float
    previous_sif_density: float
    sif_density_change: float
    current_avg_risk: float
    previous_avg_risk: float
    risk_score_change: float
    emerging_signals: List[Dict[str, Any]] = []


class SifDensityResponse(BaseModel):
    overall_density: float
    total_reports: int
    total_sif_precursors: int
    by_location: List[Dict[str, Any]] = []
    by_activity: List[Dict[str, Any]] = []
    by_department: List[Dict[str, Any]] = []
    by_life_saving_rule: List[Dict[str, Any]] = []
    by_hazard: List[Dict[str, Any]] = []
    by_barrier_failure: List[Dict[str, Any]] = []
    by_incident_type: List[Dict[str, Any]] = []


class TopRiskAreaItem(BaseModel):
    rank: int
    location_id: int
    location_name: str
    risk_level: str
    risk_score: float
    main_hazard: str
    sif_count: int
    sif_density: float = 0.0
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
    sif_density: float = 0.0
    top_hazards: List[str] = []
    open_corrective_actions: int
    recent_alerts: List[str] = []
