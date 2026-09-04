import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.models.user import User
from app.models.enums import UserRole
from app.schemas.user import UserResponse
from app.schemas.auth import LoginRequest, UserRegister, TokenResponse
from app.core.security import verify_password, get_password_hash, create_access_token
from app.auth.deps import (
    get_current_active_user,
    require_roles,
    require_worker,
    require_admin,
)
from app.services.audit import audit_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register New User Account",
    description="Registers a new user and returns user info without password hash.",
)
def register(
    user_in: UserRegister,
    db: Session = Depends(get_db),
) -> UserResponse:
    """
    Register a new user account.
    """
    # Check if user already exists
    existing = db.query(User).filter(User.email == user_in.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email address already exists.",
        )

    # Create new user
    new_user = User(
        name=user_in.name,
        email=user_in.email,
        password_hash=get_password_hash(user_in.password),
        role=user_in.role if user_in.role in [UserRole.WORKER, UserRole.ADMIN] else UserRole.WORKER,
        is_active=True,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    audit_service.log_event(
        db=db,
        action="USER_REGISTER",
        user_id=new_user.id,
        entity_type="USER",
        entity_id=str(new_user.id),
        details={"name": new_user.name, "email": new_user.email, "role": new_user.role},
    )

    logger.info(f"User registered successfully: {new_user.email} (Role: {new_user.role})")
    return new_user


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="User Login",
    description="Authenticates with email and password, returning a signed JWT Bearer token and user details.",
)
def login(
    login_data: LoginRequest,
    db: Session = Depends(get_db),
) -> TokenResponse:
    """
    Authenticate user and generate JWT token.
    """
    user = db.query(User).filter(User.email == login_data.email).first()
    if not user or not verify_password(login_data.password, user.password_hash):
        logger.warning(f"Failed login attempt for email: {login_data.email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials. Please verify your email and password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated. Please contact your system administrator.",
        )

    # Generate JWT
    token_payload = {
        "sub": str(user.id),
        "email": user.email,
        "role": user.role.value if hasattr(user.role, "value") else str(user.role),
        "name": user.name,
    }
    token = create_access_token(data=token_payload)

    audit_service.log_event(
        db=db,
        action="USER_LOGIN",
        user_id=user.id,
        entity_type="USER",
        entity_id=str(user.id),
        details={"email": user.email, "role": user.role},
    )

    logger.info(f"User logged in successfully: {user.email} ({user.role})")
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user=user,
    )


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Current Authenticated User",
    description="Returns the profile of the currently logged-in user without sensitive hashes.",
)
def get_me(
    current_user: User = Depends(get_current_active_user),
) -> UserResponse:
    """
    Retrieve current authenticated user profile.
    """
    return current_user


# ==============================================================================
# RBAC Protected Test Probes
# ==============================================================================

@router.get(
    "/rbac/worker",
    summary="Worker Access Probe",
    dependencies=[Depends(require_roles(UserRole.WORKER, UserRole.ADMIN))],
)
def rbac_worker_probe(current_user: User = Depends(get_current_active_user)):
    return {
        "status": "authorized",
        "message": f"Worker permission verified for {current_user.email}",
        "role": current_user.role,
    }


@router.get(
    "/rbac/admin",
    summary="Admin Access Probe",
    dependencies=[Depends(require_roles(UserRole.ADMIN))],
)
def rbac_admin_probe(current_user: User = Depends(get_current_active_user)):
    return {
        "status": "authorized",
        "message": f"Admin permission verified for {current_user.email}",
        "role": current_user.role,
    }
