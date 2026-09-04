import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.department import Department
from app.models.safety_report import SafetyReport
from app.models.alert import Alert
from app.models.corrective_action import CorrectiveAction
from app.models.ai_analysis import AiAnalysis
from app.models.user import User
from app.schemas.department import (
    DepartmentCreate,
    DepartmentUpdate,
    DepartmentResponse,
    DepartmentStats,
)
from app.auth.deps import get_current_active_user, require_admin
from app.services.audit import audit_service

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Departments"])


@router.get(
    "/departments",
    response_model=List[DepartmentResponse],
    summary="List Departments",
    description="Retrieve all operational departments configured in the safety system.",
)
def get_departments(
    db: Session = Depends(get_db),
) -> List[DepartmentResponse]:
    departments = db.query(Department).order_by(Department.name.asc()).all()
    return departments


@router.post(
    "/departments",
    response_model=DepartmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Department (Admin Only)",
    dependencies=[Depends(require_admin)],
)
def create_department(
    dept_in: DepartmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> DepartmentResponse:
    existing = db.query(Department).filter(Department.name.ilike(dept_in.name.strip())).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Department with name '{dept_in.name}' already exists.",
        )

    dept = Department(
        name=dept_in.name.strip(),
        description=dept_in.description.strip() if dept_in.description else None,
    )
    db.add(dept)
    db.commit()
    db.refresh(dept)

    audit_service.log_event(
        db=db,
        action="DEPARTMENT_CREATE",
        user_id=current_user.id,
        entity_type="DEPARTMENT",
        entity_id=str(dept.id),
        details={"name": dept.name, "description": dept.description},
    )

    return dept


@router.get(
    "/departments/{department_id}/stats",
    response_model=DepartmentStats,
    summary="Get Department Statistics (Admin Only)",
    dependencies=[Depends(require_admin)],
)
def get_department_stats(
    department_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> DepartmentStats:
    dept = db.query(Department).filter(Department.id == department_id).first()
    if not dept:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Department #{department_id} not found.",
        )

    reports = db.query(SafetyReport).filter(SafetyReport.department_id == dept.id).all()
    report_ids = [r.id for r in reports]

    analyses = db.query(AiAnalysis).filter(AiAnalysis.report_id.in_(report_ids)).all() if report_ids else []
    high_count = sum(1 for a in analyses if a.risk_level == "HIGH")
    crit_count = sum(1 for a in analyses if a.risk_level == "CRITICAL")
    sif_count = sum(1 for a in analyses if a.sif_precursor or a.sif_detected)

    active_alerts = db.query(Alert).filter(Alert.department_id == dept.id, Alert.status.in_(["NEW", "ACKNOWLEDGED", "IN_PROGRESS"])).count()
    open_actions = db.query(CorrectiveAction).filter(CorrectiveAction.department_id == dept.id, CorrectiveAction.status.in_(["OPEN", "ASSIGNED", "IN_PROGRESS", "OVERDUE"])).count()

    return DepartmentStats(
        id=dept.id,
        name=dept.name,
        description=dept.description,
        created_at=dept.created_at,
        total_reports=len(reports),
        high_risk_reports=high_count,
        critical_risk_reports=crit_count,
        sif_precursors=sif_count,
        active_alerts=active_alerts,
        open_actions=open_actions,
    )


@router.put(
    "/departments/{department_id}",
    response_model=DepartmentResponse,
    summary="Update Department (Admin Only)",
    dependencies=[Depends(require_admin)],
)
def update_department(
    department_id: int,
    dept_update: DepartmentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> DepartmentResponse:
    dept = db.query(Department).filter(Department.id == department_id).first()
    if not dept:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Department #{department_id} not found.",
        )

    if dept_update.name and dept_update.name.strip().lower() != dept.name.lower():
        existing = db.query(Department).filter(Department.name.ilike(dept_update.name.strip())).first()
        if existing and existing.id != dept.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Department with name '{dept_update.name}' already exists.",
            )
        dept.name = dept_update.name.strip()

    if dept_update.description is not None:
        dept.description = dept_update.description.strip()

    db.add(dept)
    db.commit()
    db.refresh(dept)

    audit_service.log_event(
        db=db,
        action="DEPARTMENT_UPDATE",
        user_id=current_user.id,
        entity_type="DEPARTMENT",
        entity_id=str(dept.id),
        details={"name": dept.name, "description": dept.description},
    )

    return dept


@router.delete(
    "/departments/{department_id}",
    summary="Delete Department (Admin Only)",
    dependencies=[Depends(require_admin)],
)
def delete_department(
    department_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> dict:
    dept = db.query(Department).filter(Department.id == department_id).first()
    if not dept:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Department #{department_id} not found.",
        )

    # Check if reports exist
    report_count = db.query(SafetyReport).filter(SafetyReport.department_id == dept.id).count()
    if report_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete department '{dept.name}' because it contains {report_count} safety report(s).",
        )

    dept_name = dept.name
    db.delete(dept)
    db.commit()

    audit_service.log_event(
        db=db,
        action="DEPARTMENT_DELETE",
        user_id=current_user.id,
        entity_type="DEPARTMENT",
        entity_id=str(department_id),
        details={"name": dept_name},
    )

    return {"status": "success", "message": f"Department '{dept_name}' deleted successfully."}
