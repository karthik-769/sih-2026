import math
import logging
from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.audit_log import AuditLog
from app.models.user import User
from app.schemas.audit_log import (
    AuditLogResponse,
    PaginatedAuditLogResponse,
)
from app.auth.deps import get_current_active_user, require_admin

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/audit-logs", tags=["Audit Logs"])


@router.get(
    "",
    response_model=PaginatedAuditLogResponse,
    summary="List Audit Logs (Admin Only)",
    dependencies=[Depends(require_admin)],
)
def list_audit_logs(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    action: Optional[str] = Query(default=None),
    entity_type: Optional[str] = Query(default=None),
    user_id: Optional[int] = Query(default=None),
    start_date: Optional[datetime] = Query(default=None),
    end_date: Optional[datetime] = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> PaginatedAuditLogResponse:
    query = db.query(AuditLog)

    if action:
        query = query.filter(AuditLog.action.ilike(f"%{action.strip()}%"))
    if entity_type:
        query = query.filter(AuditLog.entity_type == entity_type.upper())
    if user_id:
        query = query.filter(AuditLog.user_id == user_id)
    if start_date:
        query = query.filter(AuditLog.created_at >= start_date)
    if end_date:
        query = query.filter(AuditLog.created_at <= end_date)

    query = query.order_by(AuditLog.id.desc())

    total = query.count()
    total_pages = math.ceil(total / page_size) if total > 0 else 1
    offset = (page - 1) * page_size
    records = query.offset(offset).limit(page_size).all()

    items = []
    for r in records:
        items.append(
            AuditLogResponse(
                id=r.id,
                user_id=r.user_id,
                user_name=r.user.name if r.user else "System / Guest",
                user_email=r.user.email if r.user else None,
                action=r.action,
                entity_type=r.entity_type,
                entity_id=r.entity_id,
                details=r.details,
                ip_address=r.ip_address,
                created_at=r.created_at,
            )
        )

    return PaginatedAuditLogResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )
