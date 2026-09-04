import math
import logging
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.user import User
from app.models.import_batch import ImportBatch
from app.models.safety_report import SafetyReport
from app.models.enums import UserRole
from app.schemas.import_batch import (
    ImportPreviewResponse,
    ImportConfirmRequest,
    ImportConfirmResponse,
    ImportProgressResponse,
    ImportBatchResponse,
    PaginatedImportBatchResponse,
)
from app.schemas.safety_report import PaginatedSafetyReportResponse
from app.auth.deps import get_current_active_user, require_admin
from app.services.audit import audit_service
from app.services.importer.import_service import import_service

logger = logging.getLogger(__name__)

router = APIRouter()

# Restrict import endpoints to Admins (Workers denied)
authorized_importer = Depends(require_admin)


@router.post(
    "/upload",
    response_model=ImportPreviewResponse,
    status_code=status.HTTP_200_OK,
    summary="Upload & Parse Bulk Safety Reports (Admin Only)",
    description="Accepts Excel (.xlsx), CSV (.csv), or PDF (.pdf) files, parses records, performs row validation, and returns an interactive preview without saving to database.",
    dependencies=[authorized_importer],
)
def upload_and_preview_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> ImportPreviewResponse:
    return import_service.parse_and_preview_file(
        file=file,
        current_user=current_user,
        db=db,
    )


@router.post(
    "/{batch_id}/confirm",
    response_model=ImportConfirmResponse,
    status_code=status.HTTP_200_OK,
    summary="Confirm & Ingest Safety Reports Batch (Admin Only)",
    description="Saves previewed reports into database, tags source traceability, and triggers the existing AI Safety Intelligence Pipeline.",
    dependencies=[authorized_importer],
)
def confirm_import_batch(
    batch_id: str,
    confirm_req: ImportConfirmRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> ImportConfirmResponse:
    result = import_service.confirm_import_batch(
        batch_id=batch_id,
        confirm_req=confirm_req,
        current_user=current_user,
        db=db,
    )

    audit_service.log_event(
        db=db,
        action="IMPORT_BATCH_CONFIRM",
        user_id=current_user.id,
        entity_type="IMPORT_BATCH",
        entity_id=batch_id,
        details={"imported_records": result.imported_count, "batch_id": batch_id},
    )

    return result


@router.get(
    "/{batch_id}/progress",
    response_model=ImportProgressResponse,
    summary="Get Batch AI Processing Progress",
    description="Polls real-time progress of background AI classification and risk computation for an imported batch.",
    dependencies=[authorized_importer],
)
def get_batch_progress(
    batch_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> ImportProgressResponse:
    return import_service.get_batch_progress(
        batch_id=batch_id,
        db=db,
    )


@router.get(
    "",
    response_model=PaginatedImportBatchResponse,
    summary="List Historical Import Batches",
    description="Retrieves audit log of historical import batches with statistics on records imported, duplicates, errors, and AI completion.",
    dependencies=[authorized_importer],
)
def list_import_batches(
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=10, ge=1, le=100, description="Items per page"),
    file_type: Optional[str] = Query(default=None, description="Filter by file type (EXCEL, CSV, PDF)"),
    status_filter: Optional[str] = Query(default=None, alias="status", description="Filter by status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> PaginatedImportBatchResponse:
    query = db.query(ImportBatch)

    if file_type:
        query = query.filter(ImportBatch.file_type == file_type.upper())
    if status_filter:
        query = query.filter(ImportBatch.status == status_filter.upper())

    query = query.order_by(ImportBatch.id.desc())

    total_items = query.count()
    total_pages = math.ceil(total_items / page_size) if total_items > 0 else 1
    offset = (page - 1) * page_size
    batches = query.offset(offset).limit(page_size).all()

    items = []
    for b in batches:
        uploader_name = b.uploader.name if b.uploader else "System"
        uploader_email = b.uploader.email if b.uploader else None
        items.append(
            ImportBatchResponse(
                id=b.id,
                batch_id=b.batch_id,
                filename=b.filename,
                file_type=b.file_type,
                file_size_bytes=b.file_size_bytes,
                uploaded_by=b.uploaded_by,
                uploader_name=uploader_name,
                uploader_email=uploader_email,
                total_records=b.total_records,
                valid_records=b.valid_records,
                warning_records=b.warning_records,
                error_records=b.error_records,
                imported_records=b.imported_records,
                duplicate_records=b.duplicate_records,
                ai_completed_records=b.ai_completed_records,
                ai_failed_records=b.ai_failed_records,
                status=b.status,
                created_at=b.created_at,
                updated_at=b.updated_at,
            )
        )

    return PaginatedImportBatchResponse(
        items=items,
        total=total_items,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get(
    "/{batch_id}",
    response_model=dict,
    summary="Get Import Batch Details",
    description="Retrieves single import batch details including preview data and error logs.",
    dependencies=[authorized_importer],
)
def get_import_batch(
    batch_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> dict:
    if batch_id.isdigit():
        batch = db.query(ImportBatch).filter(ImportBatch.id == int(batch_id)).first()
    else:
        batch = db.query(ImportBatch).filter(ImportBatch.batch_id == batch_id).first()

    if not batch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Import Batch '{batch_id}' was not found.",
        )

    uploader_name = batch.uploader.name if batch.uploader else "System"
    return {
        "id": batch.id,
        "batch_id": batch.batch_id,
        "filename": batch.filename,
        "file_type": batch.file_type,
        "file_size_bytes": batch.file_size_bytes,
        "uploaded_by": batch.uploaded_by,
        "uploader_name": uploader_name,
        "total_records": batch.total_records,
        "valid_records": batch.valid_records,
        "warning_records": batch.warning_records,
        "error_records": batch.error_records,
        "imported_records": batch.imported_records,
        "duplicate_records": batch.duplicate_records,
        "ai_completed_records": batch.ai_completed_records,
        "ai_failed_records": batch.ai_failed_records,
        "status": batch.status,
        "preview_data": batch.preview_data or [],
        "error_log": batch.error_log or [],
        "created_at": batch.created_at.isoformat() if batch.created_at else None,
        "updated_at": batch.updated_at.isoformat() if batch.updated_at else None,
    }


@router.get(
    "/{batch_id}/reports",
    response_model=PaginatedSafetyReportResponse,
    summary="Get Reports Imported by Batch",
    description="Lists all persisted safety reports that originated from this import batch.",
    dependencies=[authorized_importer],
)
def get_batch_imported_reports(
    batch_id: str,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> PaginatedSafetyReportResponse:
    if batch_id.isdigit():
        batch = db.query(ImportBatch).filter(ImportBatch.id == int(batch_id)).first()
    else:
        batch = db.query(ImportBatch).filter(ImportBatch.batch_id == batch_id).first()

    if not batch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Import Batch '{batch_id}' was not found.",
        )

    query = db.query(SafetyReport).filter(SafetyReport.import_batch_id == batch.id)
    query = query.order_by(SafetyReport.id.desc())

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
