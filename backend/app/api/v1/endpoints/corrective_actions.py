import logging
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.user import User
from app.models.safety_report import SafetyReport
from app.models.corrective_action import CorrectiveAction
from app.models.enums import UserRole
from app.schemas.corrective_action import (
    CorrectiveActionCreate,
    CorrectiveActionUpdate,
    CorrectiveActionResponse,
    PaginatedCorrectiveActionResponse,
)
from app.services.actions.action_service import action_service
from app.services.audit import audit_service
from app.auth.deps import get_current_active_user, require_admin, require_worker

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "",
    response_model=PaginatedCorrectiveActionResponse,
    summary="List Corrective Actions",
    description="Lists corrective actions. Admins view global actions; Workers only view actions linked to their own reports.",
)
def list_corrective_actions(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    status_filter: Optional[str] = Query(default=None, alias="status", description="OPEN, ASSIGNED, IN_PROGRESS, RESOLVED, OVERDUE, CANCELLED"),
    priority_filter: Optional[str] = Query(default=None, alias="priority", description="LOW, MEDIUM, HIGH, CRITICAL"),
    department_id: Optional[int] = Query(default=None),
    location_id: Optional[int] = Query(default=None),
    assigned_to: Optional[int] = Query(default=None),
    report_id: Optional[int] = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> PaginatedCorrectiveActionResponse:
    # Worker isolation
    if current_user.role == UserRole.WORKER:
        # Get worker report IDs
        worker_report_ids = [r.id for r in db.query(SafetyReport.id).filter(SafetyReport.created_by == current_user.id).all()]
        if not worker_report_ids:
            return PaginatedCorrectiveActionResponse(items=[], total=0, page=page, page_size=page_size, total_pages=1)

        query = db.query(CorrectiveAction).filter(CorrectiveAction.report_id.in_(worker_report_ids))
        if status_filter:
            query = query.filter(CorrectiveAction.status == status_filter.upper())
        if priority_filter:
            query = query.filter(CorrectiveAction.priority == priority_filter.upper())
        if report_id:
            if report_id not in worker_report_ids:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access forbidden.")
            query = query.filter(CorrectiveAction.report_id == report_id)

        total = query.count()
        import math
        total_pages = math.ceil(total / page_size) if total > 0 else 1
        offset = (page - 1) * page_size
        actions = query.order_by(CorrectiveAction.id.desc()).offset(offset).limit(page_size).all()

        items = []
        for action in actions:
            items.append(
                CorrectiveActionResponse(
                    id=action.id,
                    action_number=action.action_number,
                    alert_id=action.alert_id,
                    pattern_id=action.pattern_id,
                    report_id=action.report_id,
                    title=action.title,
                    description=action.description,
                    recommended_action=action.recommended_action,
                    assigned_to=action.assigned_to,
                    assignee_name=action.assignee.name if action.assignee else None,
                    assignee_email=action.assignee.email if action.assignee else None,
                    department_id=action.department_id,
                    department_name=action.department.name if action.department else None,
                    location_id=action.location_id,
                    location_name=action.location.name if action.location else None,
                    priority=action.priority,
                    due_date=action.due_date,
                    status=action.status,
                    is_overdue=action.status == "OVERDUE",
                    resolution_notes=action.resolution_notes,
                    created_by=action.created_by,
                    creator_name=action.creator.name if action.creator else None,
                    completed_at=action.completed_at,
                    created_at=action.created_at,
                    updated_at=action.updated_at,
                )
            )

        return PaginatedCorrectiveActionResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    # Admin access
    return action_service.list_actions(
        page=page,
        page_size=page_size,
        status_filter=status_filter,
        priority_filter=priority_filter,
        department_id=department_id,
        location_id=location_id,
        assigned_to=assigned_to,
        db=db,
    )


@router.post(
    "",
    response_model=CorrectiveActionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Corrective Action (Admin Only)",
    dependencies=[Depends(require_admin)],
)
def create_corrective_action(
    action_in: CorrectiveActionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> CorrectiveActionResponse:
    action = action_service.create_action(
        action_in=action_in,
        current_user=current_user,
        db=db,
    )

    audit_service.log_event(
        db=db,
        action="CORRECTIVE_ACTION_CREATE",
        user_id=current_user.id,
        entity_type="CORRECTIVE_ACTION",
        entity_id=str(action.id),
        details={"action_number": action.action_number, "title": action.title, "priority": action.priority},
    )

    assignee_name = action.assignee.name if action.assignee else None
    assignee_email = action.assignee.email if action.assignee else None
    creator_name = action.creator.name if action.creator else None
    dept_name = action.department.name if action.department else None
    loc_name = action.location.name if action.location else None

    return CorrectiveActionResponse(
        id=action.id,
        action_number=action.action_number,
        alert_id=action.alert_id,
        pattern_id=action.pattern_id,
        report_id=action.report_id,
        title=action.title,
        description=action.description,
        recommended_action=action.recommended_action,
        assigned_to=action.assigned_to,
        assignee_name=assignee_name,
        assignee_email=assignee_email,
        department_id=action.department_id,
        department_name=dept_name,
        location_id=action.location_id,
        location_name=loc_name,
        priority=action.priority,
        due_date=action.due_date,
        status=action.status,
        is_overdue=action.status == "OVERDUE",
        resolution_notes=action.resolution_notes,
        created_by=action.created_by,
        creator_name=creator_name,
        completed_at=action.completed_at,
        created_at=action.created_at,
        updated_at=action.updated_at,
    )


@router.get(
    "/{action_id}",
    response_model=CorrectiveActionResponse,
    summary="Get Corrective Action Details",
)
def get_corrective_action(
    action_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> CorrectiveActionResponse:
    action_service.evaluate_overdue_actions(db)
    action = db.query(CorrectiveAction).filter(CorrectiveAction.id == action_id).first()
    if not action:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Corrective Action with ID {action_id} not found.",
        )

    # Worker isolation
    if current_user.role == UserRole.WORKER:
        if not action.report or action.report.created_by != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access forbidden: You can only view corrective actions for your own reports.",
            )

    assignee_name = action.assignee.name if action.assignee else None
    assignee_email = action.assignee.email if action.assignee else None
    creator_name = action.creator.name if action.creator else None
    dept_name = action.department.name if action.department else None
    loc_name = action.location.name if action.location else None

    return CorrectiveActionResponse(
        id=action.id,
        action_number=action.action_number,
        alert_id=action.alert_id,
        pattern_id=action.pattern_id,
        report_id=action.report_id,
        title=action.title,
        description=action.description,
        recommended_action=action.recommended_action,
        assigned_to=action.assigned_to,
        assignee_name=assignee_name,
        assignee_email=assignee_email,
        department_id=action.department_id,
        department_name=dept_name,
        location_id=action.location_id,
        location_name=loc_name,
        priority=action.priority,
        due_date=action.due_date,
        status=action.status,
        is_overdue=action.status == "OVERDUE",
        resolution_notes=action.resolution_notes,
        created_by=action.created_by,
        creator_name=creator_name,
        completed_at=action.completed_at,
        created_at=action.created_at,
        updated_at=action.updated_at,
    )


@router.patch(
    "/{action_id}",
    response_model=CorrectiveActionResponse,
    summary="Update Corrective Action (Admin Only)",
    dependencies=[Depends(require_admin)],
)
def update_corrective_action(
    action_id: int,
    action_update: CorrectiveActionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> CorrectiveActionResponse:
    action = action_service.update_action(
        action_id=action_id,
        action_update=action_update,
        current_user=current_user,
        db=db,
    )

    audit_service.log_event(
        db=db,
        action="CORRECTIVE_ACTION_UPDATE",
        user_id=current_user.id,
        entity_type="CORRECTIVE_ACTION",
        entity_id=str(action.id),
        details={"action_number": action.action_number, "status": action.status},
    )

    assignee_name = action.assignee.name if action.assignee else None
    assignee_email = action.assignee.email if action.assignee else None
    creator_name = action.creator.name if action.creator else None
    dept_name = action.department.name if action.department else None
    loc_name = action.location.name if action.location else None

    return CorrectiveActionResponse(
        id=action.id,
        action_number=action.action_number,
        alert_id=action.alert_id,
        pattern_id=action.pattern_id,
        report_id=action.report_id,
        title=action.title,
        description=action.description,
        recommended_action=action.recommended_action,
        assigned_to=action.assigned_to,
        assignee_name=assignee_name,
        assignee_email=assignee_email,
        department_id=action.department_id,
        department_name=dept_name,
        location_id=action.location_id,
        location_name=loc_name,
        priority=action.priority,
        due_date=action.due_date,
        status=action.status,
        is_overdue=action.status == "OVERDUE",
        resolution_notes=action.resolution_notes,
        created_by=action.created_by,
        creator_name=creator_name,
        completed_at=action.completed_at,
        created_at=action.created_at,
        updated_at=action.updated_at,
    )
