import logging
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.user import User
from app.schemas.reporting import SafetyReportSummary
from app.services.reporting.report_export_service import report_export_service
from app.services.audit import audit_service
from app.auth.deps import get_current_active_user, require_admin

logger = logging.getLogger(__name__)

router = APIRouter()

# Restricted to Admins
reporting_access = Depends(require_admin)


@router.get(
    "/summary",
    response_model=SafetyReportSummary,
    summary="Get Safety Executive Report Summary (Admin Only)",
    dependencies=[reporting_access],
)
def get_report_summary(
    report_type: str = Query(default="WEEKLY", description="DAILY, WEEKLY, MONTHLY, HIGH_RISK, SIF_PRECURSOR, DEPARTMENT"),
    timeframe_days: int = Query(default=30, ge=1, le=365),
    department_id: Optional[int] = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> SafetyReportSummary:
    return report_export_service.generate_summary(
        report_type=report_type,
        timeframe_days=timeframe_days,
        department_id=department_id,
        db=db,
    )


@router.get(
    "/export",
    summary="Export Safety Intelligence Data (Admin Only)",
    description="Generates safety datasets and executive reports exported to CSV, Excel (.xlsx), or PDF (.pdf).",
    dependencies=[reporting_access],
)
def export_report(
    export_type: str = Query(default="SUMMARY", description="SUMMARY, REPORTS, ACTIONS, ALERTS, USERS, IMPORTS"),
    export_format: str = Query(default="xlsx", description="csv, xlsx, pdf"),
    report_type: str = Query(default="WEEKLY"),
    timeframe_days: int = Query(default=30, ge=1, le=365),
    department_id: Optional[int] = Query(default=None),
    worker_id: Optional[int] = Query(default=None),
    risk_level: Optional[str] = Query(default=None),
    sif_status: Optional[str] = Query(default=None),
    report_status: Optional[str] = Query(default=None),
    date_from: Optional[datetime] = Query(default=None),
    date_to: Optional[datetime] = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    fmt = export_format.lower()
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    fname_base = f"safety_{export_type.lower()}_{ts}"

    file_bytes = report_export_service.export_data(
        export_type=export_type.upper(),
        export_format=fmt,
        db=db,
        department_id=department_id,
        worker_id=worker_id,
        risk_level=risk_level,
        sif_status=sif_status,
        report_status=report_status,
        date_from=date_from,
        date_to=date_to,
        timeframe_days=timeframe_days,
    )

    audit_service.log_event(
        db=db,
        action="EXPORT_DATA",
        user_id=current_user.id,
        entity_type="EXPORT",
        entity_id=export_type.upper(),
        details={"format": fmt, "export_type": export_type.upper()},
    )

    if fmt == "csv":
        return Response(
            content=file_bytes,
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={fname_base}.csv"},
        )
    elif fmt == "pdf":
        return Response(
            content=file_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={fname_base}.pdf"},
        )
    else:  # default Excel .xlsx
        return Response(
            content=file_bytes,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={fname_base}.xlsx"},
        )
