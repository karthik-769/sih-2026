from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel


class SafetyReportSummary(BaseModel):
    report_title: str
    generated_at: datetime
    timeframe: str
    total_reports: int
    risk_distribution: Dict[str, int]
    top_hazards: List[Dict[str, Any]]
    sif_precursors_count: int
    active_patterns_count: int
    active_alerts_count: int
    open_actions_count: int
    overdue_actions_count: int
    key_recommendations: List[str]
