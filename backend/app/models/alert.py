from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database.session import Base


class Alert(Base):
    """
    Represents an Early Warning Alert triggered by threshold evaluation
    on safety patterns, SIF spikes, or high-risk concentrations.
    """
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    alert_key = Column(String(100), unique=True, index=True, nullable=False)
    
    # Associated pattern (nullable if standalone event)
    pattern_id = Column(Integer, ForeignKey("patterns.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # Alert Type:
    # REPEATED_HIGH_RISK_HAZARD, REPEATED_SIF_PRECURSOR, INCREASING_TREND,
    # REPEATED_CONTROL_FAILURE, HIGH_RISK_LOCATION, SIMILAR_INCIDENTS, COMBINED_RISK
    alert_type = Column(String(50), nullable=False, index=True)
    
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    
    # Severity: LOW, MEDIUM, HIGH, CRITICAL
    severity = Column(String(50), nullable=False, default="MEDIUM", index=True)
    risk_score = Column(Float, nullable=False, default=0.0)
    
    department_id = Column(Integer, ForeignKey("departments.id", ondelete="SET NULL"), nullable=True, index=True)
    location_id = Column(Integer, ForeignKey("locations.id", ondelete="SET NULL"), nullable=True, index=True)
    hazard_category = Column(String(100), nullable=True, index=True)
    sif_category = Column(String(100), nullable=True, index=True)
    
    # Detailed data-backed explanation bullet points
    # e.g. ["6 confined-space reports recorded in last 30 days", "4 involved missing atmospheric testing", ...]
    explanation_evidence = Column(JSON, nullable=False, default=list)
    
    # Traceability
    contributing_report_ids = Column(JSON, nullable=False, default=list)
    contributing_case_ids = Column(JSON, nullable=False, default=list)
    recommended_actions = Column(JSON, nullable=False, default=list)
    
    # Status: NEW, ACKNOWLEDGED, IN_PROGRESS, RESOLVED, DISMISSED
    status = Column(String(50), nullable=False, default="NEW", index=True)
    
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)
    acknowledged_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    resolved_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    notes = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    pattern = relationship("Pattern", back_populates="alerts")
    department = relationship("Department")
    location = relationship("Location")
    acknowledger = relationship("User", foreign_keys=[acknowledged_by])
    resolver = relationship("User", foreign_keys=[resolved_by])
    corrective_actions = relationship("CorrectiveAction", back_populates="alert")

    def __repr__(self) -> str:
        return (
            f"<Alert id={self.id} key='{self.alert_key}' title='{self.title}' "
            f"severity='{self.severity}' status='{self.status}' score={self.risk_score}>"
        )
