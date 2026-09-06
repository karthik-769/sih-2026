import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.user import User
from app.schemas.analytics import (
    DashboardKpis,
    TrendPoint,
    HazardTrendItem,
    DepartmentRiskItem,
    LocationRiskItem,
    ActivityRiskItem,
    LifeSavingRuleRiskItem,
    BarrierFailureRecurrenceItem,
    TrendComparisonResponse,
    SifDensityResponse,
    TopRiskAreaItem,
    RiskMapMarker,
)
from app.schemas.ai_evaluation import AiEvaluationResponse
from app.services.analytics.analytics_service import analytics_service
from app.services.ai_evaluation.evaluation_service import ai_evaluation_service
from app.auth.deps import get_current_active_user, require_admin

logger = logging.getLogger(__name__)

router = APIRouter()

# Restricted to Admins / HSE Officers
analytics_access = Depends(require_admin)


@router.get(
    "/kpis",
    response_model=DashboardKpis,
    summary="Get Safety Command Center KPIs (Admin Only)",
    dependencies=[analytics_access],
)
def get_dashboard_kpis(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> DashboardKpis:
    return analytics_service.get_dashboard_kpis(db)


@router.get(
    "/sif-density",
    response_model=SifDensityResponse,
    summary="Get SIF Precursor Density across multiple dimensions (Admin Only)",
    dependencies=[analytics_access],
)
def get_sif_density(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> SifDensityResponse:
    return analytics_service.get_sif_density(db)


@router.get(
    "/activities",
    response_model=List[ActivityRiskItem],
    summary="Get High-Risk Operational Activities Ranked by SIF Density (Admin Only)",
    dependencies=[analytics_access],
)
def get_activity_risk(
    window: int = Query(default=30, ge=7, le=90),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> List[ActivityRiskItem]:
    return analytics_service.get_activity_risk(db, window_days=window)


@router.get(
    "/life-saving-rules",
    response_model=List[LifeSavingRuleRiskItem],
    summary="Get IOGP Life-Saving Rules Risk & SIF Density (Admin Only)",
    dependencies=[analytics_access],
)
def get_life_saving_rules_risk(
    window: int = Query(default=30, ge=7, le=90),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> List[LifeSavingRuleRiskItem]:
    return analytics_service.get_life_saving_rules_risk(db, window_days=window)


@router.get(
    "/barrier-failures",
    response_model=List[BarrierFailureRecurrenceItem],
    summary="Get Top Recurring Barrier Failures (Admin Only)",
    dependencies=[analytics_access],
)
def get_barrier_failures(
    window: int = Query(default=30, ge=7, le=90),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> List[BarrierFailureRecurrenceItem]:
    return analytics_service.get_barrier_failures_recurrence(db, window_days=window)


@router.get(
    "/trends",
    response_model=TrendComparisonResponse,
    summary="Get Multi-Period Trend & Emerging Risk Detection (Admin Only)",
    dependencies=[analytics_access],
)
def get_trends_comparison(
    window: int = Query(default=30, ge=7, le=90),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> TrendComparisonResponse:
    return analytics_service.get_trend_comparison(db, window_days=window)


@router.get(
    "/risk-trend",
    response_model=List[TrendPoint],
    summary="Get Risk Score Trend (Admin Only)",
    dependencies=[analytics_access],
)
def get_risk_trend(
    weeks: int = Query(default=4, ge=1, le=12),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> List[TrendPoint]:
    return analytics_service.get_risk_trend(db, weeks=weeks)


@router.get(
    "/hazard-trend",
    response_model=List[HazardTrendItem],
    summary="Get Top Hazards Distribution (Admin Only)",
    dependencies=[analytics_access],
)
def get_hazard_trend(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> List[HazardTrendItem]:
    return analytics_service.get_hazard_trend(db)


@router.get(
    "/sif-trend",
    response_model=Dict[str, Any],
    summary="Get SIF Precursor Analytics (Admin Only)",
    dependencies=[analytics_access],
)
def get_sif_trend(
    window: int = Query(default=30, ge=7, le=90),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Dict[str, Any]:
    return analytics_service.get_sif_trend(db, window_days=window)


@router.get(
    "/departments",
    response_model=List[DepartmentRiskItem],
    summary="Get Department Risk Comparison (Admin Only)",
    dependencies=[analytics_access],
)
def get_department_risk(
    window: int = Query(default=30, ge=7, le=90),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> List[DepartmentRiskItem]:
    return analytics_service.get_department_risk(db, window_days=window)


@router.get(
    "/locations",
    response_model=List[LocationRiskItem],
    summary="Get Location Risk & SIF Density Comparison (Admin Only)",
    dependencies=[analytics_access],
)
def get_location_risk(
    window: int = Query(default=30, ge=7, le=90),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> List[LocationRiskItem]:
    return analytics_service.get_location_risk(db, window_days=window)


@router.get(
    "/top-risk-areas",
    response_model=List[TopRiskAreaItem],
    summary="Get Top High-Risk Areas (Admin Only)",
    dependencies=[analytics_access],
)
def get_top_risk_areas(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> List[TopRiskAreaItem]:
    return analytics_service.get_top_risk_areas(db)


@router.get(
    "/risk-map",
    response_model=List[RiskMapMarker],
    summary="Get Spatial Risk Map Markers (Admin Only)",
    dependencies=[analytics_access],
)
def get_risk_map(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> List[RiskMapMarker]:
    return analytics_service.get_risk_map_markers(db)


@router.get(
    "/ai-evaluation",
    response_model=AiEvaluationResponse,
    summary="Get AI Model Evaluation & Performance Benchmarking (Admin Only)",
    dependencies=[analytics_access],
)
def get_ai_evaluation(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> AiEvaluationResponse:
    return ai_evaluation_service.evaluate(db)

