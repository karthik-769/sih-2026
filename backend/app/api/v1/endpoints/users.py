import math
import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.database.session import get_db
from app.models.user import User
from app.models.enums import UserRole
from app.schemas.user import (
    UserCreate,
    UserUpdate,
    UserResponse,
    UserPasswordReset,
    UserStatusUpdate,
    PaginatedUserResponse,
)
from app.core.security import get_password_hash
from app.auth.deps import get_current_active_user, require_admin
from app.services.audit import audit_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/users", tags=["User Management"])


@router.get(
    "",
    response_model=PaginatedUserResponse,
    summary="List Users (Admin Only)",
    dependencies=[Depends(require_admin)],
)
def list_users(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    role: Optional[UserRole] = Query(default=None),
    is_active: Optional[bool] = Query(default=None),
    search: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> PaginatedUserResponse:
    query = db.query(User)

    if role:
        query = query.filter(User.role == role)
    if is_active is not None:
        query = query.filter(User.is_active == is_active)
    if search and search.strip():
        term = f"%{search.strip()}%"
        query = query.filter(or_(User.name.ilike(term), User.email.ilike(term)))

    query = query.order_by(User.id.asc())

    total = query.count()
    total_pages = math.ceil(total / page_size) if total > 0 else 1
    offset = (page - 1) * page_size
    items = query.offset(offset).limit(page_size).all()

    return PaginatedUserResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.post(
    "",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create User (Admin Only)",
    dependencies=[Depends(require_admin)],
)
def create_user(
    user_in: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> UserResponse:
    existing = db.query(User).filter(User.email == user_in.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"A user with email '{user_in.email}' already exists.",
        )

    # Role constraint: only WORKER or ADMIN
    assigned_role = user_in.role if user_in.role in [UserRole.WORKER, UserRole.ADMIN] else UserRole.WORKER

    new_user = User(
        name=user_in.name.strip(),
        email=user_in.email.strip().lower(),
        password_hash=get_password_hash(user_in.password),
        role=assigned_role,
        is_active=user_in.is_active,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    audit_service.log_event(
        db=db,
        action="USER_CREATE",
        user_id=current_user.id,
        entity_type="USER",
        entity_id=str(new_user.id),
        details={"name": new_user.name, "email": new_user.email, "role": new_user.role},
    )

    return new_user


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    summary="Get User Details (Admin Only)",
    dependencies=[Depends(require_admin)],
)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> UserResponse:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found.",
        )
    return user


@router.put(
    "/{user_id}",
    response_model=UserResponse,
    summary="Update User (Admin Only)",
    dependencies=[Depends(require_admin)],
)
def update_user(
    user_id: int,
    user_update: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> UserResponse:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found.",
        )

    if user_update.email and user_update.email.strip().lower() != user.email:
        existing = db.query(User).filter(User.email == user_update.email.strip().lower()).first()
        if existing and existing.id != user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Email '{user_update.email}' is already in use by another account.",
            )
        user.email = user_update.email.strip().lower()

    if user_update.name is not None:
        user.name = user_update.name.strip()

    if user_update.role is not None:
        if user_update.role in [UserRole.WORKER, UserRole.ADMIN]:
            user.role = user_update.role

    if user_update.is_active is not None:
        user.is_active = user_update.is_active

    if user_update.password:
        user.password_hash = get_password_hash(user_update.password)

    db.add(user)
    db.commit()
    db.refresh(user)

    audit_service.log_event(
        db=db,
        action="USER_UPDATE",
        user_id=current_user.id,
        entity_type="USER",
        entity_id=str(user.id),
        details={"name": user.name, "email": user.email, "role": user.role, "is_active": user.is_active},
    )

    return user


@router.patch(
    "/{user_id}/status",
    response_model=UserResponse,
    summary="Activate / Deactivate User (Admin Only)",
    dependencies=[Depends(require_admin)],
)
def update_user_status(
    user_id: int,
    status_in: UserStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> UserResponse:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found.",
        )

    if user.id == current_user.id and not status_in.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot deactivate your own admin account.",
        )

    user.is_active = status_in.is_active
    db.add(user)
    db.commit()
    db.refresh(user)

    audit_service.log_event(
        db=db,
        action="USER_ACTIVATE" if status_in.is_active else "USER_DEACTIVATE",
        user_id=current_user.id,
        entity_type="USER",
        entity_id=str(user.id),
        details={"is_active": user.is_active, "target_email": user.email},
    )

    return user


@router.post(
    "/{user_id}/reset-password",
    summary="Reset User Password (Admin Only)",
    dependencies=[Depends(require_admin)],
)
def reset_user_password(
    user_id: int,
    pw_in: UserPasswordReset,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> dict:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found.",
        )

    if len(pw_in.new_password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 6 characters.",
        )

    user.password_hash = get_password_hash(pw_in.new_password)
    db.add(user)
    db.commit()

    audit_service.log_event(
        db=db,
        action="USER_PASSWORD_RESET",
        user_id=current_user.id,
        entity_type="USER",
        entity_id=str(user.id),
        details={"target_email": user.email},
    )

    return {"status": "success", "message": f"Password reset successfully for user {user.email}."}
