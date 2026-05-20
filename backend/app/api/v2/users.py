"""Users API v2 - Per-tenant user management."""
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.api.deps import DB
from app.api.v2.auth import CurrentUserV2
from app.models.app_tenant import GlobalUser
from app.models.local_user import LocalUser, EITSRole, UserRole
from app.models.membership import Membership
from app.core.security import get_password_hash

router = APIRouter()


class LocalUserResponse(BaseModel):
    id: str
    full_name: str
    department: str | None
    is_active: bool
    email: str
    roles: list[str] = []


class LocalUserCreate(BaseModel):
    email: str
    full_name: str
    department: str | None = None
    password: str


class LocalUserUpdate(BaseModel):
    full_name: str | None = None
    department: str | None = None
    is_active: bool | None = None


class RoleAssignment(BaseModel):
    role_id: str


# === E-ITS Roles Endpoints (must come before /{user_id}) ===

class EITSRoleResponse(BaseModel):
    id: str
    role_name: str
    description: str | None


@router.get("/roles", response_model=List[EITSRoleResponse])
def list_e_its_roles(db: DB, current_user = CurrentUserV2):
    """List all E-ITS roles in current tenant."""
    roles = db.query(EITSRole).filter(EITSRole.tenant_id == current_user.tenant_id).all()
    
    return [
        EITSRoleResponse(
            id=str(r.id),
            role_name=r.role_name,
            description=r.description
        )
        for r in roles
    ]


@router.get("/roles/{role_id}", response_model=EITSRoleResponse)
def get_e_its_role(role_id: UUID, db: DB, current_user = CurrentUserV2):
    """Get E-ITS role details."""
    role = db.query(EITSRole).filter(
        EITSRole.id == role_id,
        EITSRole.tenant_id == current_user.tenant_id
    ).first()
    
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found",
        )
    
    return EITSRoleResponse(
        id=str(role.id),
        role_name=role.role_name,
        description=role.description
    )


# === User endpoints ===

def _get_user_with_roles(user: LocalUser, db: DB) -> LocalUserResponse:
    """Helper to get user with roles."""
    global_user = db.query(GlobalUser).filter(GlobalUser.id == user.global_user_id).first()
    
    # Get E-ITS roles from user_roles table (by local_user.id)
    user_roles = db.query(UserRole).filter(UserRole.user_id == user.id).all()
    role_ids = [ur.role_id for ur in user_roles]
    eits_roles = db.query(EITSRole).filter(EITSRole.id.in_(role_ids)).all() if role_ids else []
    
    # Also get legacy roles from memberships table (by global_user.id)
    memberships = db.query(Membership).filter(Membership.user_id == user.global_user_id).all()
    legacy_roles = [m.role_id for m in memberships if m.role_id]
    
    # Combine both role sources
    all_roles = [r.role_name for r in eits_roles] + legacy_roles
    
    return LocalUserResponse(
        id=str(user.id),
        full_name=user.full_name,
        department=user.department,
        is_active=user.is_active,
        email=global_user.email if global_user else "",
        roles=list(set(all_roles))  # deduplicate
    )


@router.get("/", response_model=List[LocalUserResponse])
def list_users(db: DB, current_user = CurrentUserV2):
    """List all local users in current tenant."""
    users = db.query(LocalUser).filter(LocalUser.tenant_id == current_user.tenant_id).all()
    return [_get_user_with_roles(u, db) for u in users]


@router.get("/{user_id}", response_model=LocalUserResponse)
def get_user(user_id: UUID, db: DB, current_user = CurrentUserV2):
    """Get user details."""
    user = db.query(LocalUser).filter(
        LocalUser.id == user_id,
        LocalUser.tenant_id == current_user.tenant_id
    ).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    return _get_user_with_roles(user, db)


@router.post("/", response_model=LocalUserResponse)
def create_user(db: DB, request: LocalUserCreate, current_user = CurrentUserV2):
    """Create new local user in current tenant."""
    # Check if global user already exists
    existing_global = db.query(GlobalUser).filter(GlobalUser.email == request.email).first()
    
    if existing_global:
        # Check if user already has local entry in this tenant
        existing_local = db.query(LocalUser).filter(
            LocalUser.global_user_id == existing_global.id,
            LocalUser.tenant_id == current_user.tenant_id
        ).first()
        
        if existing_local:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User already exists in this tenant",
            )
        
        global_user = existing_global
    else:
        # Create new global user
        global_user = GlobalUser(
            email=request.email,
            password_hash=get_password_hash(request.password)
        )
        db.add(global_user)
        db.commit()
        db.refresh(global_user)
    
    # Create local user
    local_user = LocalUser(
        global_user_id=global_user.id,
        tenant_id=current_user.tenant_id,
        full_name=request.full_name,
        department=request.department
    )
    db.add(local_user)
    db.commit()
    db.refresh(local_user)
    
    return _get_user_with_roles(local_user, db)


@router.patch("/{user_id}", response_model=LocalUserResponse)
def update_user(user_id: UUID, request: LocalUserUpdate, db: DB, current_user = CurrentUserV2):
    """Update local user."""
    user = db.query(LocalUser).filter(
        LocalUser.id == user_id,
        LocalUser.tenant_id == current_user.tenant_id
    ).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    if request.full_name is not None:
        user.full_name = request.full_name
    if request.department is not None:
        user.department = request.department
    if request.is_active is not None:
        user.is_active = request.is_active
    
    db.commit()
    db.refresh(user)
    
    return _get_user_with_roles(user, db)


@router.delete("/{user_id}")
def delete_user(user_id: UUID, db: DB, current_user = CurrentUserV2):
    """Deactivate user (soft delete)."""
    user = db.query(LocalUser).filter(
        LocalUser.id == user_id,
        LocalUser.tenant_id == current_user.tenant_id
    ).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    user.is_active = False
    db.commit()
    
    return {"message": "User deactivated"}


@router.post("/{user_id}/roles", response_model=LocalUserResponse)
def assign_role(user_id: UUID, request: RoleAssignment, db: DB, current_user = CurrentUserV2):
    """Assign role to user."""
    user = db.query(LocalUser).filter(
        LocalUser.id == user_id,
        LocalUser.tenant_id == current_user.tenant_id
    ).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    role = db.query(EITSRole).filter(
        EITSRole.id == request.role_id,
        EITSRole.tenant_id == current_user.tenant_id
    ).first()
    
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found",
        )
    
    # Check if already assigned
    existing = db.query(UserRole).filter(
        UserRole.user_id == user.id,
        UserRole.role_id == role.id
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Role already assigned",
        )
    
    user_role = UserRole(
        user_id=user.id,
        role_id=role.id,
        granted_by=current_user.id
    )
    db.add(user_role)
    db.commit()
    
    return _get_user_with_roles(user, db)


@router.delete("/{user_id}/roles/{role_id}", response_model=LocalUserResponse)
def remove_role(user_id: UUID, role_id: UUID, db: DB, current_user = CurrentUserV2):
    """Remove role from user."""
    user = db.query(LocalUser).filter(
        LocalUser.id == user_id,
        LocalUser.tenant_id == current_user.tenant_id
    ).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    user_role = db.query(UserRole).filter(
        UserRole.user_id == user.id,
        UserRole.role_id == role_id
    ).first()
    
    if not user_role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not assigned to user",
        )
    
    db.delete(user_role)
    db.commit()
    
    return _get_user_with_roles(user, db)