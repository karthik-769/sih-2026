from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database.session import Base


class ImportBatch(Base):
    """
    Tracks bulk safety report import operations from Excel (.xlsx), CSV (.csv), and PDF (.pdf).
    Maintains full lifecycle state, row statistics, parsed preview cache, and background AI processing progress.
    """
    __tablename__ = "import_batches"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    batch_id = Column(String(50), unique=True, index=True, nullable=False)
    filename = Column(String(255), nullable=False)
    file_type = Column(String(20), nullable=False)  # EXCEL, CSV, PDF
    file_size_bytes = Column(Integer, nullable=False, default=0)
    uploaded_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)

    # Metrics
    total_records = Column(Integer, nullable=False, default=0)
    valid_records = Column(Integer, nullable=False, default=0)
    warning_records = Column(Integer, nullable=False, default=0)
    error_records = Column(Integer, nullable=False, default=0)
    failed_records = Column(Integer, nullable=False, default=0)
    imported_records = Column(Integer, nullable=False, default=0)
    duplicate_records = Column(Integer, nullable=False, default=0)
    ai_completed_records = Column(Integer, nullable=False, default=0)
    ai_failed_records = Column(Integer, nullable=False, default=0)

    # Status: UPLOADED, PREVIEWED, IMPORTING, ANALYZING, COMPLETED, COMPLETED_WITH_ERRORS, FAILED
    status = Column(String(50), nullable=False, default="UPLOADED", index=True)

    # Staged payload cache & audit logs
    preview_data = Column(JSON, nullable=False, default=list)
    error_log = Column(JSON, nullable=False, default=list)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    uploader = relationship("User", backref="import_batches")
    safety_reports = relationship("SafetyReport", back_populates="import_batch", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return (
            f"<ImportBatch id={self.id} batch_id='{self.batch_id}' "
            f"filename='{self.filename}' status='{self.status}' "
            f"total={self.total_records} imported={self.imported_records}>"
        )
