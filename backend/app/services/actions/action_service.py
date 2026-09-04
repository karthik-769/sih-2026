import logging
import math
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import or_
from fastapi import HTTPException, status

from app.models.corrective_action import CorrectiveAction
from app.models.alert import Alert
from app.models.pattern import Pattern
from app.models.safety_report import SafetyReport
from app.models.user import User
from app.schemas.corrective_action import (
    CorrectiveActionCreate,
    CorrectiveActionUpdate,
    CorrectiveActionResponse,
    PaginatedCorrectiveActionResponse,
)

logger = logging.getLogger(__name__)


class ActionService:
    """
    Manages the lifecycle of corrective actions spawned from alerts,
    patterns, or safety reports. Includes automatic overdue detection.
    """

    def generate_action_number(self, db: Session) -> str:
        count = db.query(CorrectiveAction).count() + 1
        year = datetime.now(timezone.utc).year
        return f"ACT-{year}-{count:04d}"

    def evaluate_overdue_actions(self, db: Session) -> int:
        """
        Scans open/in-progress actions and marks those past their due date as OVERDUE.
        """
        now = datetime.now(timezone.utc)
        actions = (
            db.query(CorrectiveAction)
            .filter(
                CorrectiveAction.due_date != None,
                CorrectiveAction.status.in_(["OPEN", "ASSIGNED", "IN_PROGRESS"]),
            )
            .all()
        )

        overdue_count = 0
        for act in actions:
            due = act.due_date
            if due.tzinfo is None:
                due = due.replace(tzinfo=timezone.utc)
            if due < now:
                act.status = "OVERDUE"
                db.add(act)
                overdue_count += 1

        if overdue_count > 0:
            db.commit()
            logger.info(f"Updated {overdue_count} actions to OVERDUE status.")
        return overdue_count

    def create_action(
        self,
        action_in: CorrectiveActionCreate,
        current_user: User,
        db: Session,
    ) -> CorrectiveAction:
        action_num = self.generate_action_number(db)
        init_status = "ASSIGNED" if action_in.assigned_to else "OPEN"

        # Check due date
        if action_in.due_date:
            now = datetime.now(timezone.utc)
            due = action_in.due_date
            if due.tzinfo is None:
                due = due.replace(tzinfo=timezone.utc)
            if due < now:
                init_status = "OVERDUE"

        action = CorrectiveAction(
            action_number=action_num,
            alert_id=action_in.alert_id,
            pattern_id=action_in.pattern_id,
            report_id=action_in.report_id,
            title=action_in.title.strip(),
            description=action_in.description.strip(),
            recommended_action=action_in.recommended_action.strip(),
            assigned_to=action_in.assigned_to,
            department_id=action_in.department_id,
            location_id=action_in.location_id,
            priority=action_in.priority.upper(),
            due_date=action_in.due_date,
            status=init_status,
            created_by=current_user.id,
        )

        db.add(action)

        # If spawned from an Alert, transition alert status to IN_PROGRESS
        if action_in.alert_id:
            alert = db.query(Alert).filter(Alert.id == action_in.alert_id).first()
            if alert and alert.status in ["NEW", "ACKNOWLEDGED"]:
                alert.status = "IN_PROGRESS"
                db.add(alert)

        db.commit()
        db.refresh(action)
        logger.info(f"Created Corrective Action {action.action_number} by User {current_user.email}")
        return action

    def update_action(
        self,
        action_id: int,
        action_update: CorrectiveActionUpdate,
        current_user: User,
        db: Session,
    ) -> CorrectiveAction:
        action = db.query(CorrectiveAction).filter(CorrectiveAction.id == action_id).first()
        if not action:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Corrective Action with ID {action_id} not found.",
            )

        if action_update.title is not None:
            action.title = action_update.title.strip()
        if action_update.description is not None:
            action.description = action_update.description.strip()
        if action_update.recommended_action is not None:
            action.recommended_action = action_update.recommended_action.strip()
        if action_update.assigned_to is not None:
            action.assigned_to = action_update.assigned_to
            if action.status == "OPEN":
                action.status = "ASSIGNED"
        if action_update.department_id is not None:
            action.department_id = action_update.department_id
        if action_update.location_id is not None:
            action.location_id = action_update.location_id
        if action_update.priority is not None:
            action.priority = action_update.priority.upper()
        if action_update.due_date is not None:
            action.due_date = action_update.due_date
        if action_update.resolution_notes is not None:
            action.resolution_notes = action_update.resolution_notes.strip()

        if action_update.status is not None:
            new_status = action_update.status.upper()
            action.status = new_status
            if new_status == "RESOLVED":
                action.completed_at = datetime.now(timezone.utc)
            else:
                action.completed_at = None

        # Re-check overdue status
        if action.due_date and action.status in ["OPEN", "ASSIGNED", "IN_PROGRESS"]:
            now = datetime.now(timezone.utc)
            due = action.due_date
            if due.tzinfo is None:
                due = due.replace(tzinfo=timezone.utc)
            if due < now:
                action.status = "OVERDUE"

        db.add(action)
        db.commit()
        db.refresh(action)
        return action

    def list_actions(
        self,
        page: int = 1,
        page_size: int = 10,
        status_filter: Optional[str] = None,
        priority_filter: Optional[str] = None,
        department_id: Optional[int] = None,
        location_id: Optional[int] = None,
        assigned_to: Optional[int] = None,
        db: Session = None,
    ) -> PaginatedCorrectiveActionResponse:
        self.evaluate_overdue_actions(db)

        query = db.query(CorrectiveAction)

        if status_filter:
            query = query.filter(CorrectiveAction.status == status_filter.upper())
        if priority_filter:
            query = query.filter(CorrectiveAction.priority == priority_filter.upper())
        if department_id:
            query = query.filter(CorrectiveAction.department_id == department_id)
        if location_id:
            query = query.filter(CorrectiveAction.location_id == location_id)
        if assigned_to:
            query = query.filter(CorrectiveAction.assigned_to == assigned_to)

        query = query.order_by(CorrectiveAction.id.desc())

        total_items = query.count()
        total_pages = math.ceil(total_items / page_size) if total_items > 0 else 1
        offset = (page - 1) * page_size
        actions = query.offset(offset).limit(page_size).all()

        now = datetime.now(timezone.utc)
        items = []
        for a in actions:
            is_overdue = False
            if a.due_date and a.status != "RESOLVED":
                due = a.due_date
                if due.tzinfo is None:
                    due = due.replace(tzinfo=timezone.utc)
                if due < now:
                    is_overdue = True

            assignee_name = a.assignee.name if a.assignee else None
            assignee_email = a.assignee.email if a.assignee else None
            creator_name = a.creator.name if a.creator else None
            dept_name = a.department.name if a.department else None
            loc_name = a.location.name if a.location else None

            items.append(
                CorrectiveActionResponse(
                    id=a.id,
                    action_number=a.action_number,
                    alert_id=a.alert_id,
                    pattern_id=a.pattern_id,
                    report_id=a.report_id,
                    title=a.title,
                    description=a.description,
                    recommended_action=a.recommended_action,
                    assigned_to=a.assigned_to,
                    assignee_name=assignee_name,
                    assignee_email=assignee_email,
                    department_id=a.department_id,
                    department_name=dept_name,
                    location_id=a.location_id,
                    location_name=loc_name,
                    priority=a.priority,
                    due_date=a.due_date,
                    status=a.status,
                    is_overdue=is_overdue,
                    resolution_notes=a.resolution_notes,
                    created_by=a.created_by,
                    creator_name=creator_name,
                    completed_at=a.completed_at,
                    created_at=a.created_at,
                    updated_at=a.updated_at,
                )
            )

        return PaginatedCorrectiveActionResponse(
            items=items,
            total=total_items,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )


action_service = ActionService()
