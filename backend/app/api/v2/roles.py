"""Roles API v2 - E-ITS roles and permissions."""
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.api.deps import DB
from app.api.v2.auth import CurrentUserV2

router = APIRouter()


class RoleResponse(BaseModel):
    id: str
    role_name: str
    description: str | None


class PermissionResponse(BaseModel):
    id: str
    code: str
    name: str
    category: str | None


@router.get("/", response_model=List[RoleResponse])
def list_roles(db: DB, current_user = CurrentUserV2):
    """List all E-ITS roles in current tenant."""
    from app.models.local_user import EITSRole
    
    roles = db.query(EITSRole).filter(EITSRole.tenant_id == current_user.tenant_id).all()
    
    return [
        RoleResponse(
            id=str(r.id),
            role_name=r.role_name,
            description=r.description
        )
        for r in roles
    ]


@router.get("/permissions", response_model=List[PermissionResponse])
def list_permissions(db: DB, current_user = CurrentUserV2):
    """List all available permissions."""
    from app.models.permission import Permission
    
    perms = db.query(Permission).all()
    
    return [
        PermissionResponse(
            id=p.id,
            code=p.code,
            name=p.name,
            category=p.category
        )
        for p in perms
    ]


@router.get("/{role_id}/permissions", response_model=List[PermissionResponse])
def get_role_permissions(role_id: str, db: DB, current_user = CurrentUserV2):
    """Get permissions for a specific role."""
    from app.models.role_permission import RolePermission
    from app.models.permission import Permission
    from app.models.local_user import EITSRole
    
    role = db.query(EITSRole).filter(
        EITSRole.id == role_id,
        EITSRole.tenant_id == current_user.tenant_id
    ).first()
    
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found"
        )
    
    role_perms = db.query(RolePermission).filter(RolePermission.role_id == role_id).all()
    perm_ids = [rp.permission_id for rp in role_perms]
    
    perms = db.query(Permission).filter(Permission.id.in_(perm_ids)).all() if perm_ids else []
    
    return [
        PermissionResponse(
            id=p.id,
            code=p.code,
            name=p.name,
            category=p.category
        )
        for p in perms
    ]