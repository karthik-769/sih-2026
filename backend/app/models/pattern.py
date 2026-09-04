from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database.session import Base


class Pattern(Base):
    """
    Represents a detected recurring safety hazard, SIF precursor spike,
    control failure pattern, or department/location risk concentration.
    """
    __tablename__ = "patterns"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    pattern_key = Column(String(100), unique=True, index=True, nullable=False)
    title = Column(String(255), nullable=False)
    
    # Pattern Type: HAZARD_RECURRENCE, SIF_PRECURSOR_SPIKE, CONTROL_FAILURE, LOCATION_CONCENTRATION, DEPARTMENT_RISK
    pattern_type = Column(String(50), nullable=False, index=True)
    
    hazard_category = Column(String(100), nullable=True, index=True)
    sif_category = Column(String(100), nullable=True, index=True)
    department_id = Column(Integer, ForeignKey("departments.id", ondelete="SET NULL"), nullable=True, index=True)
    location_id = Column(Integer, ForeignKey("locations.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # Scoring & Severity: LOW (0-29), MEDIUM (30-49), HIGH (50-69), CRITICAL (70-100)
    risk_score = Column(Float, nullable=False, default=0.0)
    risk_level = Column(String(50), nullable=False, default="LOW", index=True)
    
    # Quantitative Metrics
    frequency_count = Column(Integer, nullable=False, default=0)
    sif_count = Column(Integer, nullable=False, default=0)
    trend_percentage = Column(Float, nullable=False, default=0.0)  # e.g., +32.5%
    
    # Explainable factor weights breakdown
    # e.g. {"frequency_increase": 20, "sif_precursor_frequency": 30, "control_failure": 20, "location_concentration": 10}
    scoring_factors = Column(JSON, nullable=False, default=dict)
    
    # Traceability to contributing safety reports
    evidence_report_ids = Column(JSON, nullable=False, default=list)  # [1, 5, 18, 21]
    evidence_case_ids = Column(JSON, nullable=False, default=list)    # ["SIF001", "SIF005"]
    
    # Combined preventive recommendations synthesized across incidents
    recommendations = Column(JSON, nullable=False, default=list)
    
    # Lifecycle & status: ACTIVE, MONITORING, RESOLVED
    status = Column(String(50), nullable=False, default="ACTIVE", index=True)
    first_detected_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    last_detected_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    department = relationship("Department")
    location = relationship("Location")
    alerts = relationship("Alert", back_populates="pattern", cascade="all, delete-orphan")
    corrective_actions = relationship("CorrectiveAction", back_populates="pattern")

    def __repr__(self) -> str:
        return (
            f"<Pattern id={self.id} key='{self.pattern_key}' title='{self.title}' "
            f"type='{self.pattern_type}' risk_level='{self.risk_level}' score={self.risk_score}>"
        )
