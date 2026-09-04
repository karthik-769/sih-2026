import logging
from typing import Optional, Any
from sqlalchemy.orm import Session
from app.models.audit_log import AuditLog

logger = logging.getLogger(__name__)


class AuditService:
    @staticmethod
    def log_event(
        db: Session,
        action: str,
        user_id: Optional[int] = None,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        details: Optional[Any] = None,
        ip_address: Optional[str] = None,
        commit: bool = True,
    ) -> Optional[AuditLog]:
        try:
            log_entry = AuditLog(
                user_id=user_id,
                action=action,
                entity_type=entity_type,
                entity_id=str(entity_id) if entity_id is not None else None,
                details=details,
                ip_address=ip_address,
            )
            db.add(log_entry)
            if commit:
                db.commit()
                db.refresh(log_entry)
            return log_entry
        except Exception as e:
            logger.error(f"Failed to record audit log for action '{action}': {e}")
            return None


audit_service = AuditService()
