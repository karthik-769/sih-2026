import math
import logging
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.user import User
from app.models.pattern import Pattern
from app.models.safety_report import SafetyReport
from app.models.enums import UserRole
from app.schemas.pattern import PatternResponse, PaginatedPatternResponse
from app.schemas.safety_report import SafetyReportResponse
from app.services.patterns.pattern_engine import pattern_engine
from app.auth.deps import get_current_active_user, require_admin

logger = logging.getLogger(__name__)

router = APIRouter()

# Restricted to Admins (Workers blocked)
safety_analytics_access = Depends(require_admin)


@router.get(
    "",
    response_model=PaginatedPatternResponse,
    summary="List Safety Patterns",
    description="Retrieves paginated recurring hazard patterns, SIF spikes, and risk concentrations.",
    dependencies=[safety_analytics_access],
)
def list_patterns(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    pattern_type: Optional[str] = Query(default=None, description="Filter by type (e.g. HAZARD_RECURRENCE, LOCATION_CONCENTRATION)"),
    risk_level: Optional[str] = Query(default=None, description="Filter by severity (LOW, MEDIUM, HIGH, CRITICAL)"),
    status_filter: Optional[str] = Query(default=None, alias="status", description="Filter by status (ACTIVE, MONITORING, RESOLVED)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> PaginatedPatternResponse:
    query = db.query(Pattern)

    if pattern_type:
        query = query.filter(Pattern.pattern_type == pattern_type.upper())
    if risk_level:
        query = query.filter(Pattern.risk_level == risk_level.upper())
    if status_filter:
        query = query.filter(Pattern.status == status_filter.upper())

    query = query.order_by(Pattern.risk_score.desc(), Pattern.id.desc())

    total_items = query.count()
    total_pages = math.ceil(total_items / page_size) if total_items > 0 else 1
    offset = (page - 1) * page_size
    patterns = query.offset(offset).limit(page_size).all()

    items = []
    for p in patterns:
        items.append(
            PatternResponse(
                id=p.id,
                pattern_key=p.pattern_key,
                title=p.title,
                pattern_type=p.pattern_type,
                hazard_category=p.hazard_category,
                sif_category=p.sif_category,
                department_id=p.department_id,
                department_name=p.department.name if p.department else None,
                location_id=p.location_id,
                location_name=p.location.name if p.location else None,
                risk_score=p.risk_score,
                risk_level=p.risk_level,
                frequency_count=p.frequency_count,
                sif_count=p.sif_count,
                trend_percentage=p.trend_percentage,
                scoring_factors=p.scoring_factors or {},
                evidence_report_ids=p.evidence_report_ids or [],
                evidence_case_ids=p.evidence_case_ids or [],
                recommendations=p.recommendations or [],
                status=p.status,
                first_detected_at=p.first_detected_at,
                last_detected_at=p.last_detected_at,
                created_at=p.created_at,
                updated_at=p.updated_at,
            )
        )

    return PaginatedPatternResponse(
        items=items,
        total=total_items,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get(
    "/{pattern_id}",
    response_model=dict,
    summary="Get Pattern Details",
    description="Retrieves pattern details with full list of contributing safety reports and evidence.",
    dependencies=[safety_analytics_access],
)
def get_pattern_details(
    pattern_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> dict:
    p = db.query(Pattern).filter(Pattern.id == pattern_id).first()
    if not p:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pattern #{pattern_id} was not found.",
        )

    # Fetch contributing report models
    reports = []
    if p.evidence_report_ids:
        reps = db.query(SafetyReport).filter(SafetyReport.id.in_(p.evidence_report_ids)).all()
        for r in reps:
            reports.append({
                "id": r.id,
                "case_id": r.case_id,
                "job_role": r.job_role,
                "task": r.task,
                "description": r.description,
                "incident_type": r.incident_type.value if hasattr(r.incident_type, "value") else str(r.incident_type),
                "department_name": r.department.name if r.department else None,
                "location_name": r.location.name if r.location else None,
                "reported_at": r.reported_at.isoformat() if r.reported_at else None,
                "processing_status": r.processing_status.value if hasattr(r.processing_status, "value") else str(r.processing_status),
            })

    return {
        "id": p.id,
        "pattern_key": p.pattern_key,
        "title": p.title,
        "pattern_type": p.pattern_type,
        "hazard_category": p.hazard_category,
        "sif_category": p.sif_category,
        "department_id": p.department_id,
        "department_name": p.department.name if p.department else None,
        "location_id": p.location_id,
        "location_name": p.location.name if p.location else None,
        "risk_score": p.risk_score,
        "risk_level": p.risk_level,
        "frequency_count": p.frequency_count,
        "sif_count": p.sif_count,
        "trend_percentage": p.trend_percentage,
        "scoring_factors": p.scoring_factors or {},
        "evidence_report_ids": p.evidence_report_ids or [],
        "evidence_case_ids": p.evidence_case_ids or [],
        "recommendations": p.recommendations or [],
        "contributing_reports": reports,
        "status": p.status,
        "first_detected_at": p.first_detected_at.isoformat() if p.first_detected_at else None,
        "last_detected_at": p.last_detected_at.isoformat() if p.last_detected_at else None,
        "created_at": p.created_at.isoformat() if p.created_at else None,
        "updated_at": p.updated_at.isoformat() if p.updated_at else None,
    }


@router.post(
    "/recompute",
    summary="Recompute All Safety Patterns",
    description="Forces a full scan of safety reports to detect patterns and evaluate early warnings.",
    dependencies=[safety_analytics_access],
)
def recompute_patterns(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> dict:
    from app.services.patterns.early_warning_engine import early_warning_engine
    patterns = pattern_engine.analyze_all_patterns(db)
    alerts = early_warning_engine.evaluate_patterns_and_generate_alerts(db)
    return {
        "status": "success",
        "patterns_detected": len(patterns),
        "alerts_generated": len(alerts),
    }
