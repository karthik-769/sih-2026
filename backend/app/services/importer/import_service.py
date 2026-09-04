import os
import io
import math
import logging
import threading
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Tuple
from fastapi import UploadFile, HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.database.session import SessionLocal
from app.models.user import User
from app.models.department import Department
from app.models.location import Location
from app.models.safety_report import SafetyReport
from app.models.import_batch import ImportBatch
from app.models.enums import IncidentType, ProcessingStatus
from app.schemas.import_batch import (
    ImportedRowPreview,
    ImportPreviewResponse,
    ImportConfirmRequest,
    ImportConfirmResponse,
    ImportProgressResponse,
)
from app.services.importer.parsers.excel_parser import ExcelParser
from app.services.importer.parsers.csv_parser import CsvParser
from app.services.importer.parsers.pdf_parser import PdfParser
from app.services.case_id import generate_unique_case_id
from app.services.analysis import analysis_service

logger = logging.getLogger(__name__)


class ImportService:
    """
    Coordinates end-to-end bulk safety report ingestion:
    File validation -> Parsing -> Domain entity resolution -> Preview & Validation ->
    Transactional Database Import -> Background AI Processing Pipeline.
    """

    @classmethod
    def generate_batch_id(cls, db: Session) -> str:
        """Generates a human-friendly unique Batch ID like BATCH-2026-001."""
        current_year = datetime.now().year
        prefix = f"BATCH-{current_year}-"
        last_batch = (
            db.query(ImportBatch)
            .filter(ImportBatch.batch_id.like(f"{prefix}%"))
            .order_by(ImportBatch.id.desc())
            .first()
        )
        if last_batch and last_batch.batch_id:
            try:
                num = int(last_batch.batch_id.split("-")[-1])
                return f"{prefix}{num + 1:03d}"
            except ValueError:
                pass
        count = db.query(ImportBatch).count()
        return f"{prefix}{count + 1:03d}"

    def parse_and_preview_file(
        self,
        file: UploadFile,
        current_user: User,
        db: Session,
    ) -> ImportPreviewResponse:
        """
        Validates uploaded file, parses rows, performs row-level validation and duplicate detection,
        persists preview cache in import_batches, and returns interactive preview data.
        """
        filename = file.filename or "uploaded_file"
        ext = os.path.splitext(filename)[1].lower()

        # 1. Validate File Type
        if ext not in settings.ALLOWED_IMPORT_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file format '{ext}'. Allowed formats: {settings.ALLOWED_IMPORT_EXTENSIONS}",
            )

        # 2. Read File Bytes & Validate Size
        file_bytes = file.file.read()
        file_size_bytes = len(file_bytes)
        max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
        if file_size_bytes > max_bytes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File size ({round(file_size_bytes / (1024*1024), 2)} MB) exceeds maximum allowed upload size of {settings.MAX_UPLOAD_SIZE_MB} MB.",
            )

        if file_size_bytes == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded file is empty.",
            )

        # 3. Parse File according to format
        file_type = "EXCEL" if ext in [".xlsx", ".xls"] else "CSV" if ext == ".csv" else "PDF"
        try:
            if file_type == "EXCEL":
                raw_records = ExcelParser.parse_excel_bytes(file_bytes, filename=filename)
            elif file_type == "CSV":
                raw_records = CsvParser.parse_csv_bytes(file_bytes, filename=filename)
            else:
                raw_records = PdfParser.parse_pdf_bytes(file_bytes, filename=filename)
        except Exception as parse_err:
            logger.error(f"Failed to parse {filename}: {parse_err}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Failed to parse {file_type} file '{filename}': {str(parse_err)}",
            )

        if not raw_records:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"No safety report records could be extracted from '{filename}'. Please ensure the file contains valid columns or structured text.",
            )

        # 4. Resolve Master Data & Validate Rows
        departments = db.query(Department).all()
        locations = db.query(Location).all()
        dept_name_map = {d.name.strip().lower(): d for d in departments}
        loc_name_map = {l.name.strip().lower(): l for l in locations}

        # Pre-fetch existing Case IDs for duplicate detection
        existing_cases = {r.case_id.strip().upper(): r.id for r in db.query(SafetyReport.case_id, SafetyReport.id).all() if r.case_id}

        parsed_rows: List[ImportedRowPreview] = []
        valid_cnt = 0
        warn_cnt = 0
        err_cnt = 0
        dup_cnt = 0

        # Track duplicates within the uploaded file itself
        seen_in_file_cases = set()

        for idx, rec in enumerate(raw_records, start=1):
            row_num = rec.get("source_row") or idx
            page_num = rec.get("source_page")
            desc = (rec.get("description") or "").strip()
            case_id_raw = (rec.get("case_id") or "").strip()
            job_role = (rec.get("job_role") or "Maintenance Worker").strip()
            task = (rec.get("task") or "Operational Safety Task").strip()
            raw_dept = (rec.get("department") or "").strip()
            raw_loc = (rec.get("location") or "").strip()
            raw_type = rec.get("incident_type") or "UNSAFE_ACT"
            raw_date = rec.get("date_time")

            messages: List[str] = []
            is_dup = False
            row_status = "VALID"

            # Check Description (mandatory)
            if not desc or len(desc) < 8:
                row_status = "ERROR"
                messages.append("Description is missing or too short (minimum 8 characters required).")

            # Check Case ID & Duplicate
            if case_id_raw:
                c_upper = case_id_raw.upper()
                if c_upper in existing_cases:
                    is_dup = True
                    dup_cnt += 1
                    messages.append(f"Case ID '{case_id_raw}' already exists in database (will skip or overwrite according to policy).")
                    if row_status != "ERROR":
                        row_status = "WARNING"
                elif c_upper in seen_in_file_cases:
                    is_dup = True
                    dup_cnt += 1
                    messages.append(f"Duplicate Case ID '{case_id_raw}' appears multiple times within this file.")
                    if row_status != "ERROR":
                        row_status = "WARNING"
                else:
                    seen_in_file_cases.add(c_upper)

            # Resolve Department
            resolved_dept_id = None
            resolved_dept_name = raw_dept
            if raw_dept:
                matched_dept = dept_name_map.get(raw_dept.lower())
                if not matched_dept:
                    # Partial match
                    for k, v in dept_name_map.items():
                        if k in raw_dept.lower() or raw_dept.lower() in k:
                            matched_dept = v
                            break
                if matched_dept:
                    resolved_dept_id = matched_dept.id
                    resolved_dept_name = matched_dept.name
                else:
                    messages.append(f"Department '{raw_dept}' not found in registry (defaulting to primary department).")
                    if row_status == "VALID":
                        row_status = "WARNING"
                    resolved_dept_id = departments[0].id if departments else 1
            else:
                messages.append("Department not specified (assigned to primary department).")
                if row_status == "VALID":
                    row_status = "WARNING"
                resolved_dept_id = departments[0].id if departments else 1

            # Resolve Location
            resolved_loc_id = None
            resolved_loc_name = raw_loc
            if raw_loc:
                matched_loc = loc_name_map.get(raw_loc.lower())
                if not matched_loc:
                    for k, v in loc_name_map.items():
                        if k in raw_loc.lower() or raw_loc.lower() in k:
                            matched_loc = v
                            break
                if matched_loc:
                    resolved_loc_id = matched_loc.id
                    resolved_loc_name = matched_loc.name
                else:
                    messages.append(f"Location '{raw_loc}' not found in registry (defaulting to Unit A).")
                    if row_status == "VALID":
                        row_status = "WARNING"
                    resolved_loc_id = locations[0].id if locations else 1
            else:
                messages.append("Location not specified (assigned to Unit A).")
                if row_status == "VALID":
                    row_status = "WARNING"
                resolved_loc_id = locations[0].id if locations else 1

            # Validate Incident Type
            valid_types = {"UNSAFE_ACT", "UNSAFE_CONDITION", "NEAR_MISS", "SAFETY_OBSERVATION"}
            if raw_type not in valid_types:
                messages.append(f"Incident type '{raw_type}' normalized to UNSAFE_ACT.")
                raw_type = "UNSAFE_ACT"
                if row_status == "VALID":
                    row_status = "WARNING"

            if row_status == "ERROR":
                err_cnt += 1
            elif row_status == "WARNING":
                warn_cnt += 1
            else:
                valid_cnt += 1

            row_preview = ImportedRowPreview(
                row_number=row_num,
                page_number=page_num,
                case_id=case_id_raw or None,
                job_role=job_role,
                department_id=resolved_dept_id,
                department_name=resolved_dept_name or "Mechanical",
                location_id=resolved_loc_id,
                location_name=resolved_loc_name or "Unit A",
                task=task,
                incident_type=raw_type,
                reported_at=raw_date,
                description=desc,
                validation_status=row_status,
                validation_messages=messages,
                is_duplicate=is_dup,
            )
            parsed_rows.append(row_preview)

        # 5. Persist ImportBatch in Database (Status: PREVIEWED)
        batch_id = self.generate_batch_id(db)
        batch = ImportBatch(
            batch_id=batch_id,
            filename=filename,
            file_type=file_type,
            file_size_bytes=file_size_bytes,
            uploaded_by=current_user.id,
            total_records=len(parsed_rows),
            valid_records=valid_cnt,
            warning_records=warn_cnt,
            error_records=err_cnt,
            imported_records=0,
            duplicate_records=dup_cnt,
            ai_completed_records=0,
            ai_failed_records=0,
            status="PREVIEWED",
            preview_data=[r.model_dump() for r in parsed_rows],
            error_log=[],
        )
        db.add(batch)
        db.commit()
        db.refresh(batch)

        logger.info(
            f"Import batch {batch_id} created: {len(parsed_rows)} rows parsed "
            f"({valid_cnt} valid, {warn_cnt} warning, {err_cnt} error, {dup_cnt} duplicate)"
        )

        return ImportPreviewResponse(
            batch_id=batch.batch_id,
            filename=filename,
            file_type=file_type,
            file_size_bytes=file_size_bytes,
            total_records=len(parsed_rows),
            valid_records=valid_cnt,
            warning_records=warn_cnt,
            error_records=err_cnt,
            duplicate_records=dup_cnt,
            rows=parsed_rows,
        )

    def confirm_import_batch(
        self,
        batch_id: str,
        confirm_req: ImportConfirmRequest,
        current_user: User,
        db: Session,
    ) -> ImportConfirmResponse:
        """
        Commits valid/warning safety reports into PostgreSQL/SQLite with source traceability
        and launches asynchronous background AI analysis processing.
        """
        batch = db.query(ImportBatch).filter(ImportBatch.batch_id == batch_id).first()
        if not batch:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Import Batch '{batch_id}' was not found.",
            )

        if batch.status in ["IMPORTING", "ANALYZING", "COMPLETED", "COMPLETED_WITH_ERRORS"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Import Batch '{batch_id}' has already been confirmed and processed (Status: {batch.status}).",
            )

        preview_rows = batch.preview_data or []
        if not preview_rows:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"No preview records found in batch '{batch_id}'.",
            )

        duplicate_strategy = (confirm_req.duplicate_strategy or "SKIP").upper()
        selected_indices = set(confirm_req.selected_row_indices) if confirm_req.selected_row_indices else None

        # Fetch existing Case IDs
        existing_report_map = {
            r.case_id.strip().upper(): r
            for r in db.query(SafetyReport).all()
            if r.case_id
        }

        imported_reports: List[SafetyReport] = []
        skipped_dups = 0
        replaced_dups = 0
        error_cnt = 0

        for row_dict in preview_rows:
            row_num = row_dict.get("row_number")
            if selected_indices is not None and row_num not in selected_indices:
                continue

            # Skip rows with ERROR status
            if row_dict.get("validation_status") == "ERROR":
                error_cnt += 1
                continue

            case_id_val = row_dict.get("case_id")
            is_duplicate = row_dict.get("is_duplicate", False)

            # Handle Duplicates
            if is_duplicate and case_id_val:
                c_key = case_id_val.strip().upper()
                if duplicate_strategy == "SKIP":
                    skipped_dups += 1
                    logger.info(f"Skipping duplicate report {case_id_val} per duplicate policy")
                    continue
                elif duplicate_strategy == "REPLACE" and c_key in existing_report_map:
                    # Overwrite existing report
                    rep = existing_report_map[c_key]
                    rep.job_role = row_dict.get("job_role") or rep.job_role
                    rep.department_id = row_dict.get("department_id") or rep.department_id
                    rep.location_id = row_dict.get("location_id") or rep.location_id
                    rep.task = row_dict.get("task") or rep.task
                    rep.incident_type = IncidentType(row_dict.get("incident_type")) if row_dict.get("incident_type") else rep.incident_type
                    rep.description = row_dict.get("description") or rep.description
                    rep.source_type = batch.file_type
                    rep.source_file = batch.filename
                    rep.source_row = row_num
                    rep.source_page = row_dict.get("page_number")
                    rep.import_batch_id = batch.id
                    rep.processing_status = ProcessingStatus.SUBMITTED
                    db.add(rep)
                    imported_reports.append(rep)
                    replaced_dups += 1
                    continue

            # Generate unique Case ID if missing
            if not case_id_val or not str(case_id_val).strip():
                assigned_case_id = generate_unique_case_id(db)
            else:
                assigned_case_id = str(case_id_val).strip()

            # Parse Reported Date
            reported_date = datetime.now(timezone.utc)
            if row_dict.get("reported_at"):
                try:
                    reported_date = datetime.fromisoformat(str(row_dict.get("reported_at")).replace("Z", "+00:00"))
                except Exception:
                    reported_date = datetime.now(timezone.utc)

            new_report = SafetyReport(
                case_id=assigned_case_id,
                job_role=row_dict.get("job_role") or "Maintenance Worker",
                department_id=row_dict.get("department_id") or 1,
                location_id=row_dict.get("location_id") or 1,
                task=row_dict.get("task") or "Operational Safety Task",
                incident_type=IncidentType(row_dict.get("incident_type") or "UNSAFE_ACT"),
                description=row_dict.get("description", "").strip(),
                reported_at=reported_date,
                created_by=current_user.id,
                processing_status=ProcessingStatus.SUBMITTED,
                source_type=batch.file_type,
                source_file=batch.filename,
                source_row=row_num,
                source_page=row_dict.get("page_number"),
                import_batch_id=batch.id,
            )
            db.add(new_report)
            imported_reports.append(new_report)
            existing_report_map[assigned_case_id.upper()] = new_report

        # Update batch record
        batch.imported_records = len(imported_reports)
        batch.duplicate_records = skipped_dups + replaced_dups
        batch.failed_records = error_cnt
        batch.status = "ANALYZING" if imported_reports else "COMPLETED"
        db.add(batch)
        db.commit()

        for rep in imported_reports:
            db.refresh(rep)
        db.refresh(batch)

        logger.info(
            f"Batch {batch_id} confirmed: {len(imported_reports)} reports stored in database. "
            f"Launching background AI processing pipeline..."
        )

        # 6. Launch Background Asynchronous AI Analysis
        report_ids = [rep.id for rep in imported_reports]
        if report_ids:
            threading.Thread(
                target=self._run_background_ai_pipeline,
                args=(batch.id, report_ids),
                daemon=True,
            ).start()

        return ImportConfirmResponse(
            batch_id=batch.batch_id,
            status=batch.status,
            message=f"Successfully imported {len(imported_reports)} safety reports. AI pipeline triggered in background.",
            total_requested=len(preview_rows),
            imported_count=len(imported_reports),
            skipped_duplicates_count=skipped_dups,
            replaced_duplicates_count=replaced_dups,
            error_count=error_cnt,
            ai_processing_status="PROCESSING" if report_ids else "COMPLETED",
        )

    def _run_background_ai_pipeline(self, batch_db_id: int, report_ids: List[int]) -> None:
        """
        Worker thread that processes imported reports sequentially through the existing Milestone 2 AI Pipeline.
        Updates progress metrics in the import_batches table.
        """
        logger.info(f"Background AI worker started for Batch ID #{batch_db_id} with {len(report_ids)} reports")
        db = SessionLocal()
        try:
            batch = db.query(ImportBatch).filter(ImportBatch.id == batch_db_id).first()
            if not batch:
                logger.error(f"Background AI worker: Batch #{batch_db_id} not found.")
                return

            completed_count = 0
            failed_count = 0

            for r_id in report_ids:
                try:
                    analysis_service.process_report_analysis(
                        report_id=r_id,
                        db=db,
                        raise_on_failure=False,
                    )
                    completed_count += 1
                except Exception as ai_err:
                    logger.warning(f"Background AI processing failed for Report #{r_id}: {ai_err}")
                    failed_count += 1

                # Update batch progress periodically
                batch.ai_completed_records = completed_count
                batch.ai_failed_records = failed_count
                db.add(batch)
                db.commit()

            # Finalize status
            if failed_count > 0:
                batch.status = "COMPLETED_WITH_ERRORS"
            else:
                batch.status = "COMPLETED"
            db.add(batch)
            db.commit()
            logger.info(f"Background AI worker finished for Batch #{batch_db_id}: {completed_count} completed, {failed_count} failed")

        except Exception as exc:
            logger.error(f"Fatal background AI worker exception on batch #{batch_db_id}: {exc}", exc_info=True)
            try:
                batch = db.query(ImportBatch).filter(ImportBatch.id == batch_db_id).first()
                if batch:
                    batch.status = "COMPLETED_WITH_ERRORS"
                    db.add(batch)
                    db.commit()
            except Exception:
                pass
        finally:
            db.close()

    def get_batch_progress(self, batch_id: str, db: Session) -> ImportProgressResponse:
        """
        Retrieves real-time AI analysis progress for an import batch.
        """
        batch = db.query(ImportBatch).filter(ImportBatch.batch_id == batch_id).first()
        if not batch:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Import Batch '{batch_id}' was not found.",
            )

        total_imported = batch.imported_records or 0
        ai_done = batch.ai_completed_records + batch.ai_failed_records
        progress_pct = (ai_done / total_imported * 100.0) if total_imported > 0 else 100.0
        progress_pct = round(min(progress_pct, 100.0), 1)

        is_finished = batch.status in ["COMPLETED", "COMPLETED_WITH_ERRORS", "FAILED"]

        msg = f"AI Analysis in progress: {batch.ai_completed_records} of {total_imported} completed."
        if is_finished:
            msg = f"Import and AI Analysis finished. {batch.ai_completed_records} successfully analyzed, {batch.ai_failed_records} failed."

        return ImportProgressResponse(
            batch_id=batch.batch_id,
            status=batch.status,
            total_records=batch.total_records,
            imported_records=batch.imported_records,
            duplicate_records=batch.duplicate_records,
            failed_records=batch.failed_records,
            ai_completed_records=batch.ai_completed_records,
            ai_failed_records=batch.ai_failed_records,
            progress_percentage=progress_pct,
            is_finished=is_finished,
            message=msg,
        )


# Global Singleton
import_service = ImportService()
