from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database.session import Base
from app.models.enums import IncidentType, ProcessingStatus


class SafetyReport(Base):
    __tablename__ = "safety_reports"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    case_id = Column(String(50), unique=True, index=True, nullable=False)
    job_role = Column(String(100), nullable=False)
    department_id = Column(Integer, ForeignKey("departments.id", ondelete="RESTRICT"), nullable=False, index=True)
    location_id = Column(Integer, ForeignKey("locations.id", ondelete="RESTRICT"), nullable=False, index=True)
    task = Column(String(255), nullable=False)
    incident_type = Column(
        Enum(IncidentType, name="incident_type", native_enum=False),
        nullable=False,
    )
    description = Column(Text, nullable=False)
    reported_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    processing_status = Column(
        Enum(ProcessingStatus, name="processing_status", native_enum=False),
        nullable=False,
        default=ProcessingStatus.SUBMITTED,
    )

    # Source Traceability
    source_type = Column(String(50), nullable=False, default="MANUAL")  # MANUAL, EXCEL, CSV, PDF
    source_file = Column(String(255), nullable=True)
    source_row = Column(Integer, nullable=True)
    source_page = Column(Integer, nullable=True)
    import_batch_id = Column(Integer, ForeignKey("import_batches.id", ondelete="SET NULL"), nullable=True, index=True)

    # OIL Domain & Precursor Metadata
    activity = Column(String(100), nullable=True, index=True)
    activity_category = Column(String(100), nullable=True, index=True)
    site = Column(String(100), nullable=True)
    field = Column(String(100), nullable=True)
    installation = Column(String(100), nullable=True)
    actual_consequence = Column(String(100), nullable=True, default="No injury")
    potential_consequence = Column(String(255), nullable=True)
    fatality_potential = Column(Boolean, nullable=True, default=False)
    life_saving_rule = Column(String(100), nullable=True, index=True)
    failed_barrier = Column(String(255), nullable=True)
    is_sif = Column(Boolean, nullable=True, default=None)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    department = relationship("Department", back_populates="safety_reports")
    location = relationship("Location", back_populates="safety_reports")
    reporter = relationship("User", back_populates="safety_reports")
    ai_analysis = relationship("AiAnalysis", back_populates="report", uselist=False, cascade="all, delete-orphan")
    import_batch = relationship("ImportBatch", back_populates="safety_reports")

    def __repr__(self) -> str:
        return f"<SafetyReport id={self.id} case_id='{self.case_id}' type='{self.incident_type}' status='{self.processing_status}'>"
