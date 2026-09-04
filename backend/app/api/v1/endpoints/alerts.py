import math
import logging
from typing import Optional, List
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.user import User
from app.models.alert import Alert
from app.models.safety_report import SafetyReport
from app.models.corrective_action import CorrectiveAction
from app.models.enums import UserRole
from app.schemas.alert import AlertResponse, AlertUpdate, PaginatedAlertResponse
from app.auth.deps import get_current_active_user, require_admin

logger = logging.getLogger(__name__)

router = APIRouter()

# Restricted to Admins (Workers blocked)
safety_alerts_access = Depends(require_admin)


@router.get(
    "",
    response_model=PaginatedAlertResponse,
    summary="List Early Warning Alerts",
    description="Retrieves active and historical early warning alerts with severity filters.",
    dependencies=[safety_alerts_access],
)
def list_alerts(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    severity: Optional[str] = Query(default=None, description="LOW, MEDIUM, HIGH, CRITICAL"),
    status_filter: Optional[str] = Query(default=None, alias="status", description="NEW, ACKNOWLEDGED, IN_PROGRESS, RESOLVED, DISMISSED"),
    department_id: Optional[int] = Query(default=None),
    location_id: Optional[int] = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> PaginatedAlertResponse:
    query = db.query(Alert)

    if severity:
        query = query.filter(Alert.severity == severity.upper())
    if status_filter:
        query = query.filter(Alert.status == status_filter.upper())
    if department_id:
        query = query.filter(Alert.department_id == department_id)
    if location_id:
        query = query.filter(Alert.location_id == location_id)

    query = query.order_by(Alert.risk_score.desc(), Alert.id.desc())

    total_items = query.count()
    total_pages = math.ceil(total_items / page_size) if total_items > 0 else 1
    offset = (page - 1) * page_size
    alerts = query.offset(offset).limit(page_size).all()

    items = []
    for a in alerts:
        items.append(
            AlertResponse(
                id=a.id,
                alert_key=a.alert_key,
                pattern_id=a.pattern_id,
                alert_type=a.alert_type,
                title=a.title,
                description=a.description,
                severity=a.severity,
                risk_score=a.risk_score,
                department_id=a.department_id,
                department_name=a.department.name if a.department else None,
                location_id=a.location_id,
                location_name=a.location.name if a.location else None,
                hazard_category=a.hazard_category,
                sif_category=a.sif_category,
                explanation_evidence=a.explanation_evidence or [],
                contributing_report_ids=a.contributing_report_ids or [],
                contributing_case_ids=a.contributing_case_ids or [],
                recommended_actions=a.recommended_actions or [],
                status=a.status,
                acknowledged_at=a.acknowledged_at,
                acknowledged_by=a.acknowledged_by,
                acknowledged_by_name=a.acknowledger.name if a.acknowledger else None,
                resolved_at=a.resolved_at,
                resolved_by=a.resolved_by,
                resolved_by_name=a.resolver.name if a.resolver else None,
                notes=a.notes,
                created_at=a.created_at,
                updated_at=a.updated_at,
            )
        )

    return PaginatedAlertResponse(
        items=items,
        total=total_items,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get(
    "/{alert_id}",
    response_model=dict,
    summary="Get Alert Details",
    description="Retrieves full alert information including evidence explanations, contributing reports, and associated corrective actions.",
    dependencies=[safety_alerts_access],
)
def get_alert_details(
    alert_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> dict:
    a = db.query(Alert).filter(Alert.id == alert_id).first()
    if not a:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Alert #{alert_id} not found.",
        )

    # Fetch contributing reports
    reports = []
    if a.contributing_report_ids:
        reps = db.query(SafetyReport).filter(SafetyReport.id.in_(a.contributing_report_ids)).all()
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
            })

    # Fetch corrective actions linked to this alert
    actions = []
    linked_actions = db.query(CorrectiveAction).filter(CorrectiveAction.alert_id == a.id).all()
    for act in linked_actions:
        actions.append({
            "id": act.id,
            "action_number": act.action_number,
            "title": act.title,
            "priority": act.priority,
            "status": act.status,
            "assignee_name": act.assignee.name if act.assignee else None,
            "due_date": act.due_date.isoformat() if act.due_date else None,
        })

    return {
        "id": a.id,
        "alert_key": a.alert_key,
        "pattern_id": a.pattern_id,
        "alert_type": a.alert_type,
        "title": a.title,
        "description": a.description,
        "severity": a.severity,
        "risk_score": a.risk_score,
        "department_id": a.department_id,
        "department_name": a.department.name if a.department else None,
        "location_id": a.location_id,
        "location_name": a.location.name if a.location else None,
        "hazard_category": a.hazard_category,
        "sif_category": a.sif_category,
        "explanation_evidence": a.explanation_evidence or [],
        "contributing_report_ids": a.contributing_report_ids or [],
        "contributing_case_ids": a.contributing_case_ids or [],
        "recommended_actions": a.recommended_actions or [],
        "contributing_reports": reports,
        "corrective_actions": actions,
        "status": a.status,
        "acknowledged_at": a.acknowledged_at.isoformat() if a.acknowledged_at else None,
        "acknowledged_by": a.acknowledged_by,
        "acknowledged_by_name": a.acknowledger.name if a.acknowledger else None,
        "resolved_at": a.resolved_at.isoformat() if a.resolved_at else None,
        "resolved_by": a.resolved_by,
        "resolved_by_name": a.resolver.name if a.resolver else None,
        "notes": a.notes,
        "created_at": a.created_at.isoformat() if a.created_at else None,
        "updated_at": a.updated_at.isoformat() if a.updated_at else None,
    }


@router.patch(
    "/{alert_id}",
    response_model=AlertResponse,
    summary="Update Alert Status",
    description="Allows Safety Officers or Supervisors to acknowledge, resolve, or dismiss an alert.",
    dependencies=[safety_alerts_access],
)
def update_alert(
    alert_id: int,
    alert_update: AlertUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> AlertResponse:
    a = db.query(Alert).filter(Alert.id == alert_id).first()
    if not a:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Alert #{alert_id} not found.",
        )

    now = datetime.now(timezone.utc)
    if alert_update.status:
        new_st = alert_update.status.upper()
        a.status = new_st
        if new_st == "ACKNOWLEDGED":
            a.acknowledged_at = now
            a.acknowledged_by = current_user.id
        elif new_st in ["RESOLVED", "DISMISSED"]:
            a.resolved_at = now
            a.resolved_by = current_user.id

    if alert_update.notes is not None:
        a.notes = alert_update.notes.strip()

    db.add(a)
    db.commit()
    db.refresh(a)

    return AlertResponse(
        id=a.id,
        alert_key=a.alert_key,
        pattern_id=a.pattern_id,
        alert_type=a.alert_type,
        title=a.title,
        description=a.description,
        severity=a.severity,
        risk_score=a.risk_score,
        department_id=a.department_id,
        department_name=a.department.name if a.department else None,
        location_id=a.location_id,
        location_name=a.location.name if a.location else None,
        hazard_category=a.hazard_category,
        sif_category=a.sif_category,
        explanation_evidence=a.explanation_evidence or [],
        contributing_report_ids=a.contributing_report_ids or [],
        contributing_case_ids=a.contributing_case_ids or [],
        recommended_actions=a.recommended_actions or [],
        status=a.status,
        acknowledged_at=a.acknowledged_at,
        acknowledged_by=a.acknowledged_by,
        acknowledged_by_name=a.acknowledger.name if a.acknowledger else None,
        resolved_at=a.resolved_at,
        resolved_by=a.resolved_by,
        resolved_by_name=a.resolver.name if a.resolver else None,
        notes=a.notes,
        created_at=a.created_at,
        updated_at=a.updated_at,
    )
