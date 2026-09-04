from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database.session import Base


class CorrectiveAction(Base):
    """
    Represents an actionable preventive or corrective task spawned from
    an Early Warning Alert, recurring pattern, or critical safety report.
    """
    __tablename__ = "corrective_actions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    action_number = Column(String(50), unique=True, index=True, nullable=False)
    
    alert_id = Column(Integer, ForeignKey("alerts.id", ondelete="SET NULL"), nullable=True, index=True)
    pattern_id = Column(Integer, ForeignKey("patterns.id", ondelete="SET NULL"), nullable=True, index=True)
    report_id = Column(Integer, ForeignKey("safety_reports.id", ondelete="SET NULL"), nullable=True, index=True)
    
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    recommended_action = Column(Text, nullable=False)
    
    assigned_to = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    department_id = Column(Integer, ForeignKey("departments.id", ondelete="SET NULL"), nullable=True, index=True)
    location_id = Column(Integer, ForeignKey("locations.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # Priority: LOW, MEDIUM, HIGH, CRITICAL
    priority = Column(String(50), nullable=False, default="MEDIUM", index=True)
    
    due_date = Column(DateTime(timezone=True), nullable=True, index=True)
    
    # Status: OPEN, ASSIGNED, IN_PROGRESS, RESOLVED, OVERDUE, CANCELLED
    status = Column(String(50), nullable=False, default="OPEN", index=True)
    
    resolution_notes = Column(Text, nullable=True)
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    alert = relationship("Alert", back_populates="corrective_actions")
    pattern = relationship("Pattern", back_populates="corrective_actions")
    report = relationship("SafetyReport")
    department = relationship("Department")
    location = relationship("Location")
    assignee = relationship("User", foreign_keys=[assigned_to])
    creator = relationship("User", foreign_keys=[created_by])

    def __repr__(self) -> str:
        return (
            f"<CorrectiveAction id={self.id} number='{self.action_number}' "
            f"title='{self.title}' priority='{self.priority}' status='{self.status}'>"
        )
