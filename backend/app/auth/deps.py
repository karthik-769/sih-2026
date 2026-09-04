import logging
from typing import Callable, List, Union
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.core.security import decode_access_token
from app.database.session import get_db
from app.models.user import User
from app.models.enums import UserRole

logger = logging.getLogger(__name__)

# HTTPBearer security scheme (supports Authorization: Bearer <token>)
security = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: Union[HTTPAuthorizationCredentials, None] = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    """
    Extracts and validates JWT Bearer token and returns the current authenticated user.
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials were not provided.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials or token has expired.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials or token payload is invalid.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if str(user_id).isdigit():
        user = db.query(User).filter(User.id == int(user_id)).first()
    else:
        user = db.query(User).filter(User.email == str(user_id)).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authenticated user account not found.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Ensures that the authenticated user account is active.
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user account.",
        )
    return current_user


def require_roles(*allowed_roles: Union[UserRole, str]) -> Callable:
    """
    Reusable role-based authorization dependency factory.
    Example usage:
        @router.get("/admin-only", dependencies=[Depends(require_roles(UserRole.ADMIN))])
    """
    # Normalize roles to string values
    role_strings = {r.value if hasattr(r, "value") else str(r) for r in allowed_roles}

    def role_checker(current_user: User = Depends(get_current_active_user)) -> User:
        user_role_str = current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role)
        if user_role_str not in role_strings:
            logger.warning(
                f"Forbidden access: User {current_user.email} (role: {user_role_str}) "
                f"attempted to access endpoint requiring {role_strings}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access forbidden: Insufficient role permissions. Allowed roles: {list(role_strings)}",
            )
        return current_user

    return role_checker


# Convenient role shortcut dependencies
require_worker = require_roles(UserRole.WORKER, UserRole.ADMIN)
require_admin = require_roles(UserRole.ADMIN)
