"""API dependencies."""
from typing import Annotated

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User
from app.models.role import Role
from app.core.security import get_current_user as _get_current_user

DB = Annotated[Session, Depends(get_db)]
CurrentUser = Annotated[User, Depends(_get_current_user)]


def require_role(role_code: str):
    """Dependency to require a specific role."""
    def role_checker(current_user: CurrentUser, db: DB):
        membership = current_user.memberships.first()
        if not membership or membership.role.code != role_code:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{role_code}' required",
            )
        return current_user
    return role_checker


def require_admin(current_user: CurrentUser):
    """Require admin role."""
    membership = current_user.memberships.first()
    if not membership or membership.role.code != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin role required",
        )
    return current_user