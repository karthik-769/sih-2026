from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, ConfigDict


class ImportedRowPreview(BaseModel):
    row_number: int = Field(..., description="1-indexed row number in source file")
    page_number: Optional[int] = Field(default=None, description="Page number for PDF files")
    case_id: Optional[str] = Field(default=None, description="Extracted or auto-generated Case ID")
    job_role: Optional[str] = Field(default="Worker", description="Job role or title")
    department_id: Optional[int] = Field(default=None, description="Resolved department ID")
    department_name: Optional[str] = Field(default=None, description="Raw or mapped department name")
    location_id: Optional[int] = Field(default=None, description="Resolved plant location ID")
    location_name: Optional[str] = Field(default=None, description="Raw or mapped location name")
    task: Optional[str] = Field(default=None, description="Task being performed")
    incident_type: Optional[str] = Field(default="UNSAFE_ACT", description="Incident category")
    reported_at: Optional[str] = Field(default=None, description="Reported date/time string")
    description: str = Field(..., description="Verbatim incident/observation narrative")
    validation_status: str = Field(default="VALID", description="VALID, WARNING, or ERROR")
    validation_messages: List[str] = Field(default_factory=list, description="Explanations for warning or error state")
    is_duplicate: bool = Field(default=False, description="True if case_id already exists in database")
    is_sif: Optional[bool] = Field(default=None, description="Ground truth SIF label if present")
    life_saving_rule: Optional[str] = Field(default=None, description="Ground truth Life-Saving Rule if present")
    failed_barrier: Optional[str] = Field(default=None, description="Ground truth failed barrier if present")
    actual_consequence: Optional[str] = Field(default=None, description="Ground truth actual consequence if present")
    potential_consequence: Optional[str] = Field(default=None, description="Ground truth potential consequence if present")
    fatality_potential: Optional[bool] = Field(default=None, description="Ground truth fatality potential if present")


class ImportPreviewResponse(BaseModel):
    batch_id: str
    filename: str
    file_type: str
    file_size_bytes: int
    total_records: int
    valid_records: int
    warning_records: int
    error_records: int
    duplicate_records: int
    rows: List[ImportedRowPreview] = Field(default_factory=list)


class ImportConfirmRequest(BaseModel):
    duplicate_strategy: str = Field(
        default="SKIP",
        description="Strategy for handling duplicates: 'SKIP' or 'REPLACE'"
    )
    selected_row_indices: Optional[List[int]] = Field(
        default=None,
        description="Optional subset of row numbers to import. If None, imports all non-error rows."
    )


class ImportConfirmResponse(BaseModel):
    batch_id: str
    status: str
    message: str
    total_requested: int
    imported_count: int
    skipped_duplicates_count: int
    replaced_duplicates_count: int
    error_count: int
    ai_processing_status: str = Field(
        default="QUEUED",
        description="QUEUED, PROCESSING, or COMPLETED"
    )


class ImportProgressResponse(BaseModel):
    batch_id: str
    status: str  # UPLOADED, PREVIEWED, IMPORTING, ANALYZING, COMPLETED, COMPLETED_WITH_ERRORS, FAILED
    total_records: int
    imported_records: int
    duplicate_records: int
    failed_records: int
    ai_completed_records: int
    ai_failed_records: int
    progress_percentage: float = 0.0
    is_finished: bool = False
    message: Optional[str] = None


class ImportBatchResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    batch_id: str
    filename: str
    file_type: str
    file_size_bytes: int
    uploaded_by: Optional[int] = None
    uploader_name: Optional[str] = None
    uploader_email: Optional[str] = None
    total_records: int
    valid_records: int
    warning_records: int
    error_records: int
    imported_records: int
    duplicate_records: int
    ai_completed_records: int
    ai_failed_records: int
    status: str
    created_at: datetime
    updated_at: datetime


class PaginatedImportBatchResponse(BaseModel):
    items: List[ImportBatchResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
