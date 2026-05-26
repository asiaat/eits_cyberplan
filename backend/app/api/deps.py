"""API dependencies."""
from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.db.session import get_db, get_session_maker
from app.models.user import User
from app.models.role import Role
from app.core.security import decode_token
from app.schemas.user import TenantUser


def get_session_local():
    """Get session maker for dependency injection."""
    return get_session_maker()


DB = Annotated[Session, Depends(get_db)]

bearer = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = credentials.credentials
    payload = decode_token(token)
    user_id: str = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = db.query(User).filter(User.id == UUID(user_id)).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def get_current_tenant_user(
    current_user: CurrentUser,
    db: DB,
) -> TenantUser:
    """Get current user with resolved tenant_id from membership."""
    membership = current_user.memberships.first()
    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tenant membership",
        )
    if not membership.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tenant associated with membership",
        )
    return TenantUser(
        id=current_user.id,
        email=current_user.email,
        name=current_user.name,
        tenant_id=membership.tenant_id,
        role_code=membership.role.code if membership.role else "viewer",
    )


TenantUserDep = Annotated[TenantUser, Depends(get_current_tenant_user)]


def require_role(role_code: str):
    """Require a specific role for the current user's tenant membership."""
    def role_checker(tenant_user: TenantUserDep):
        if tenant_user.role_code != role_code:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{role_code}' required",
            )
        return tenant_user
    return role_checker


def require_admin(tenant_user: TenantUserDep):
    """Require admin role."""
    if tenant_user.role_code != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin role required",
        )
    return tenant_user
