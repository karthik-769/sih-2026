import logging
import math
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.database.session import get_db
from app.models.safety_report import SafetyReport
from app.models.department import Department
from app.models.location import Location
from app.models.user import User
from app.models.enums import UserRole, IncidentType, ProcessingStatus
from app.schemas.safety_report import (
    SafetyReportCreate,
    SafetyReportUpdate,
    SafetyReportResponse,
    PaginatedSafetyReportResponse,
)
from app.schemas.ai_analysis import (
    AiAnalysisResponse,
    AiAnalysisTriggerResponse,
    SimilarIncidentsResponse,
    HseReviewRequest,
    HseReviewResponse,
)
from app.services.case_id import generate_unique_case_id
from app.services.analysis import analysis_service
from app.services.audit import audit_service
from app.auth.deps import get_current_active_user, require_admin

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "",
    response_model=SafetyReportResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit New Safety Report",
    description="Captures worker safety report, stores it, automatically executes the AI intelligence pipeline, and records audit log.",
)
def create_report(
    report_in: SafetyReportCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> SafetyReportResponse:
    """
    Submits, stores a safety report, and automatically executes AI analysis.
    """
    # 1. Verify Department exists
    dept = db.query(Department).filter(Department.id == report_in.department_id).first()
    if not dept:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Department with ID {report_in.department_id} does not exist.",
        )

    # 2. Verify Location exists
    loc = db.query(Location).filter(Location.id == report_in.location_id).first()
    if not loc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Location with ID {report_in.location_id} does not exist.",
        )

    # 3. Resolve or Generate Case ID
    if report_in.case_id and report_in.case_id.strip():
        assigned_case_id = report_in.case_id.strip()
        existing = db.query(SafetyReport).filter(SafetyReport.case_id == assigned_case_id).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Case ID '{assigned_case_id}' already exists. Please choose a different Case ID or leave blank to auto-generate.",
            )
    else:
        assigned_case_id = generate_unique_case_id(db)

    # 4. Resolve reported_at timestamp
    reported_at = report_in.reported_at or datetime.now(timezone.utc)

    # 5. Create Safety Report model instance (raw description preserved intact)
    new_report = SafetyReport(
        case_id=assigned_case_id,
        job_role=report_in.job_role.strip(),
        department_id=report_in.department_id,
        location_id=report_in.location_id,
        task=report_in.task.strip(),
        incident_type=report_in.incident_type,
        description=report_in.description.strip(),
        reported_at=reported_at,
        activity=report_in.activity,
        activity_category=report_in.activity_category,
        site=report_in.site,
        field=report_in.field,
        installation=report_in.installation,
        actual_consequence=report_in.actual_consequence or "No injury",
        potential_consequence=report_in.potential_consequence,
        fatality_potential=report_in.fatality_potential or False,
        life_saving_rule=report_in.life_saving_rule,
        created_by=current_user.id,
        processing_status=ProcessingStatus.SUBMITTED,
    )

    db.add(new_report)
    db.commit()
    db.refresh(new_report)

    # 6. Automatic AI Safety Intelligence Analysis Execution
    try:
        analysis_service.process_report_analysis(
            report_id=new_report.id,
            db=db,
            raise_on_failure=False,
        )
        db.refresh(new_report)
    except Exception as ai_err:
        logger.warning(f"Automatic AI analysis on report creation note: {ai_err}")

    # 7. Audit Log
    audit_service.log_event(
        db=db,
        action="REPORT_CREATE",
        user_id=current_user.id,
        entity_type="REPORT",
        entity_id=str(new_report.id),
        details={"case_id": new_report.case_id, "task": new_report.task, "incident_type": new_report.incident_type},
    )

    logger.info(
        f"Safety Report created & analyzed: {new_report.case_id} by User {current_user.email} (Status: {new_report.processing_status})"
    )

    return new_report


@router.get(
    "",
    response_model=PaginatedSafetyReportResponse,
    summary="List Safety Reports",
    description="Retrieves paginated safety reports with filtering and strict RBAC scoping.",
)
def list_reports(
    page: int = Query(default=1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(default=10, ge=1, le=100, description="Items per page"),
    department_id: Optional[int] = Query(default=None, description="Filter by Department ID"),
    location_id: Optional[int] = Query(default=None, description="Filter by Location ID"),
    incident_type: Optional[IncidentType] = Query(default=None, description="Filter by Incident Type"),
    processing_status: Optional[ProcessingStatus] = Query(default=None, description="Filter by Processing Status"),
    import_batch_id: Optional[int] = Query(default=None, description="Filter by Import Batch ID"),
    search: Optional[str] = Query(default=None, description="Search term across task, description, case_id, or job_role"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> PaginatedSafetyReportResponse:
    """
    Lists safety reports with filtering, pagination, and RBAC scoping.
    Workers only see their own submitted reports.
    """
    query = db.query(SafetyReport)

    # RBAC Scoping: Workers can only view their own reports
    if current_user.role == UserRole.WORKER:
        query = query.filter(SafetyReport.created_by == current_user.id)

    # Apply Filters
    if department_id is not None:
        query = query.filter(SafetyReport.department_id == department_id)
    if location_id is not None:
        query = query.filter(SafetyReport.location_id == location_id)
    if incident_type is not None:
        query = query.filter(SafetyReport.incident_type == incident_type)
    if processing_status is not None:
        query = query.filter(SafetyReport.processing_status == processing_status)
    if import_batch_id is not None:
        query = query.filter(SafetyReport.import_batch_id == import_batch_id)

    # Free-text Search
    if search and search.strip():
        term = f"%{search.strip()}%"
        query = query.filter(
            or_(
                SafetyReport.case_id.ilike(term),
                SafetyReport.task.ilike(term),
                SafetyReport.description.ilike(term),
                SafetyReport.job_role.ilike(term),
            )
        )

    # Sorting: Most recent first
    query = query.order_by(SafetyReport.reported_at.desc(), SafetyReport.id.desc())

    total_items = query.count()
    total_pages = math.ceil(total_items / page_size) if total_items > 0 else 1
    offset = (page - 1) * page_size
    items = query.offset(offset).limit(page_size).all()

    return PaginatedSafetyReportResponse(
        items=items,
        total=total_items,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get(
    "/{report_id}",
    response_model=SafetyReportResponse,
    summary="Get Safety Report Details",
    description="Retrieves a single safety report by ID or Case ID with strict RBAC.",
)
def get_report(
    report_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> SafetyReportResponse:
    """
    Retrieves safety report details with RBAC scoping.
    """
    if report_id.isdigit():
        report = db.query(SafetyReport).filter(SafetyReport.id == int(report_id)).first()
    else:
        report = db.query(SafetyReport).filter(SafetyReport.case_id == report_id).first()

    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Safety Report '{report_id}' was not found.",
        )

    # RBAC Scoping: Worker cannot view other workers' reports
    if current_user.role == UserRole.WORKER and report.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: You can only view your own submitted safety reports.",
        )

    return report


@router.put(
    "/{report_id}",
    response_model=SafetyReportResponse,
    summary="Edit Safety Report (Admin Only)",
    description="Allows Admin to edit report fields and triggers automated AI re-analysis so intelligence remains synchronized.",
    dependencies=[Depends(require_admin)],
)
def update_report(
    report_id: str,
    report_update: SafetyReportUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> SafetyReportResponse:
    if report_id.isdigit():
        report = db.query(SafetyReport).filter(SafetyReport.id == int(report_id)).first()
    else:
        report = db.query(SafetyReport).filter(SafetyReport.case_id == report_id).first()

    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Safety Report '{report_id}' was not found.",
        )

    # Apply updates
    if report_update.job_role is not None:
        report.job_role = report_update.job_role.strip()
    if report_update.department_id is not None:
        dept = db.query(Department).filter(Department.id == report_update.department_id).first()
        if not dept:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Department not found.")
        report.department_id = report_update.department_id
    if report_update.location_id is not None:
        loc = db.query(Location).filter(Location.id == report_update.location_id).first()
        if not loc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Location not found.")
        report.location_id = report_update.location_id
    if report_update.task is not None:
        report.task = report_update.task.strip()
    if report_update.incident_type is not None:
        report.incident_type = report_update.incident_type
    if report_update.description is not None:
        report.description = report_update.description.strip()
    if report_update.processing_status is not None:
        report.processing_status = report_update.processing_status

    db.add(report)
    db.commit()
    db.refresh(report)

    # Re-run AI analysis if text or core data changed
    try:
        analysis_service.process_report_analysis(report_id=report.id, db=db, raise_on_failure=False)
        db.refresh(report)
    except Exception as e:
        logger.warning(f"AI re-analysis note after edit: {e}")

    audit_service.log_event(
        db=db,
        action="REPORT_UPDATE",
        user_id=current_user.id,
        entity_type="REPORT",
        entity_id=str(report.id),
        details={"case_id": report.case_id, "task": report.task, "incident_type": report.incident_type},
    )

    return report


@router.post(
    "/{report_id}/analyze",
    response_model=AiAnalysisTriggerResponse,
    status_code=status.HTTP_200_OK,
    summary="Trigger AI Analysis on Safety Report",
    description="Executes the AI processing pipeline for a safety report, persisting structured intelligence.",
)
def trigger_report_analysis(
    report_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> AiAnalysisTriggerResponse:
    """
    Triggers AI processing pipeline for the given safety report.
    """
    if report_id.isdigit():
        report = db.query(SafetyReport).filter(SafetyReport.id == int(report_id)).first()
    else:
        report = db.query(SafetyReport).filter(SafetyReport.case_id == report_id).first()

    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Safety Report '{report_id}' was not found.",
        )

    # RBAC Scoping: Workers can only trigger analysis for their own reports
    if current_user.role == UserRole.WORKER and report.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: You can only trigger analysis on your own reports.",
        )

    try:
        analysis_record = analysis_service.process_report_analysis(
            report_id=report.id,
            db=db,
            raise_on_failure=True,
        )
    except Exception as exc:
        logger.error(f"Analysis trigger failed for report {report.id}: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI pipeline processing failed: {str(exc)}. Report marked as FAILED to allow retry.",
        )

    audit_service.log_event(
        db=db,
        action="AI_ANALYSIS_TRIGGER",
        user_id=current_user.id,
        entity_type="REPORT",
        entity_id=str(report.id),
        details={"case_id": report.case_id, "risk_level": analysis_record.risk_level, "risk_score": analysis_record.risk_score},
    )

    return AiAnalysisTriggerResponse(
        message="AI safety intelligence analysis completed successfully.",
        report_id=report.id,
        processing_status=report.processing_status.value if hasattr(report.processing_status, "value") else str(report.processing_status),
        analysis=analysis_record,
    )


@router.get(
    "/{report_id}/analysis",
    response_model=AiAnalysisResponse,
    summary="Get AI Analysis for Safety Report",
    description="Retrieves the structured safety intelligence and risk analysis result for a given safety report.",
)
def get_report_analysis(
    report_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> AiAnalysisResponse:
    """
    Retrieves stored AI analysis for a report.
    """
    if report_id.isdigit():
        report = db.query(SafetyReport).filter(SafetyReport.id == int(report_id)).first()
    else:
        report = db.query(SafetyReport).filter(SafetyReport.case_id == report_id).first()

    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Safety Report '{report_id}' was not found.",
        )

    # RBAC Scoping
    if current_user.role == UserRole.WORKER and report.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: You can only view analysis of your own reports.",
        )

    from app.models.ai_analysis import AiAnalysis
    analysis = db.query(AiAnalysis).filter(AiAnalysis.report_id == report.id).first()

    if not analysis:
        # If not analyzed yet, run analysis on-demand
        try:
            analysis = analysis_service.process_report_analysis(report_id=report.id, db=db, raise_on_failure=False)
        except Exception as e:
            logger.warning(f"On-demand analysis fallback failed: {e}")

    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No AI analysis found for Safety Report '{report_id}'. The report may be pending analysis or failed.",
        )

    return analysis


@router.get(
    "/{report_id}/similar",
    response_model=SimilarIncidentsResponse,
    summary="Get Semantically Similar Historical Reports",
    description="Retrieves semantically similar historical safety reports using vector cosine similarity.",
)
def get_similar_reports(
    report_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> SimilarIncidentsResponse:
    """
    Retrieves semantically similar incidents with risk and SIF precursor breakdown.
    """
    if report_id.isdigit():
        report = db.query(SafetyReport).filter(SafetyReport.id == int(report_id)).first()
    else:
        report = db.query(SafetyReport).filter(SafetyReport.case_id == report_id).first()

    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Safety Report '{report_id}' was not found.",
        )

    # RBAC Scoping
    if current_user.role == UserRole.WORKER and report.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: You can only view similar incidents for your own reports.",
        )

    try:
        similar_data = analysis_service.get_similar_incidents(report_id=report.id, db=db)
        return SimilarIncidentsResponse(**similar_data)
    except Exception as exc:
        logger.error(f"Failed to calculate similar incidents for report {report.id}: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not calculate similar incidents: {str(exc)}",
        )


@router.post(
    "/{report_id}/review",
    response_model=HseReviewResponse,
    summary="HSE Human-in-the-Loop Review (Confirm / Override)",
    description="Allows HSE officers to review, confirm, or override AI safety intelligence classifications.",
)
def review_report_analysis(
    report_id: str,
    review_in: HseReviewRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> HseReviewResponse:
    """
    Submits an HSE human confirmation or override decision for an AI safety assessment.
    """
    if report_id.isdigit():
        report = db.query(SafetyReport).filter(SafetyReport.id == int(report_id)).first()
    else:
        report = db.query(SafetyReport).filter(SafetyReport.case_id == report_id).first()

    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Safety Report '{report_id}' was not found.",
        )

    try:
        updated_analysis = analysis_service.review_analysis(
            report_id=report.id,
            action=review_in.action,
            reviewer_id=current_user.id,
            sif_level=review_in.sif_level,
            life_saving_rule=review_in.life_saving_rule,
            risk_score=review_in.risk_score,
            comment=review_in.comment,
            db=db,
        )

        # Audit logging
        audit_service.log_event(
            db=db,
            action="HSE_REVIEW",
            user_id=current_user.id,
            entity_type="REPORT_ANALYSIS",
            entity_id=str(report.id),
            details={
                "action": review_in.action,
                "sif_level": updated_analysis.sif_level,
                "review_status": updated_analysis.review_status,
                "comment": review_in.comment,
            },
        )

        return HseReviewResponse(
            success=True,
            message=f"AI Safety Assessment successfully {updated_analysis.review_status.lower()}.",
            report_id=report.id,
            review_status=updated_analysis.review_status,
            reviewed_at=updated_analysis.reviewed_at or datetime.utcnow(),
            final_decision=updated_analysis.final_hse_decision or {},
        )
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(val_err),
        )
    except Exception as exc:
        logger.error(f"HSE Review failed for report {report.id}: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Review processing failed: {str(exc)}",
        )

