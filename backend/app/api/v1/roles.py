"""Roles and permissions API endpoints."""
from typing import List, Optional
from pydantic import BaseModel

from fastapi import APIRouter, Depends, HTTPException
from uuid import UUID

from app.api.deps import DB, CurrentUser
from app.models.role import Role
from app.models.permission import Permission
from app.models.membership import Membership
from app.core.permissions import get_role_permissions, set_role_permissions, get_user_roles, get_user_permissions

router = APIRouter()


class RoleCreate(BaseModel):
    code: str
    name: str
    description: Optional[str] = None


class RoleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class RoleResponse(BaseModel):
    id: str
    code: str
    name: str
    description: Optional[str]
    is_default: str

    model_config = {"from_attributes": True}


class PermissionResponse(BaseModel):
    id: str
    code: str
    name: str
    description: Optional[str]
    category: str

    model_config = {"from_attributes": True}


class RolePermissionsUpdate(BaseModel):
    permission_ids: List[str]


class UserRoleAssign(BaseModel):
    role_id: str


@router.get("/", response_model=List[RoleResponse])
def list_roles(db: DB, current_user: CurrentUser):
    """List all roles."""
    roles = db.query(Role).all()
    return roles


@router.get("/permissions", response_model=List[PermissionResponse])
def list_permissions(db: DB, current_user: CurrentUser, category: Optional[str] = None):
    """List all permissions, optionally filtered by category."""
    query = db.query(Permission)
    if category:
        query = query.filter(Permission.category == category)
    return query.all()


@router.get("/permissions/categories")
def list_permission_categories(db: DB, current_user: CurrentUser):
    """List all permission categories."""
    perms = db.query(Permission.category).distinct().all()
    return [p[0] for p in perms]


@router.post("/", response_model=RoleResponse)
def create_role(role_in: RoleCreate, db: DB, current_user: CurrentUser):
    """Create a new role."""
    # Check if code already exists
    existing = db.query(Role).filter(Role.code == role_in.code).first()
    if existing:
        raise HTTPException(status_code=400, detail="Role code already exists")

    role = Role(
        id=role_in.code,
        code=role_in.code,
        name=role_in.name,
        description=role_in.description,
        is_default="false",
    )
    db.add(role)
    db.commit()
    db.refresh(role)
    return role


@router.get("/{role_id}", response_model=RoleResponse)
def get_role(role_id: str, db: DB, current_user: CurrentUser):
    """Get a role by ID."""
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    return role


@router.patch("/{role_id}", response_model=RoleResponse)
def update_role(role_id: str, role_in: RoleUpdate, db: DB, current_user: CurrentUser):
    """Update a role."""
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")

    if role_in.name is not None:
        role.name = role_in.name
    if role_in.description is not None:
        role.description = role_in.description

    db.commit()
    db.refresh(role)
    return role


@router.delete("/{role_id}")
def delete_role(role_id: str, db: DB, current_user: CurrentUser):
    """Delete a role."""
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")

    if role.is_default == "true":
        raise HTTPException(status_code=400, detail="Cannot delete default E-ITS roles")

    # Check if role is in use
    memberships = db.query(Membership).filter(Membership.role_id == role_id).count()
    if memberships > 0:
        raise HTTPException(status_code=400, detail="Cannot delete role that is assigned to users")

    db.delete(role)
    db.commit()
    return {"message": "Role deleted"}


@router.get("/{role_id}/permissions", response_model=List[PermissionResponse])
def get_role_permissions_endpoint(role_id: str, db: DB, current_user: CurrentUser):
    """Get permissions for a role."""
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")

    return get_role_permissions(db, role_id)


@router.post("/{role_id}/permissions")
def set_role_permissions_endpoint(role_id: str, data: RolePermissionsUpdate, db: DB, current_user: CurrentUser):
    """Set permissions for a role."""
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")

    # Verify all permissions exist
    perms = db.query(Permission).filter(Permission.id.in_(data.permission_ids)).all()
    if len(perms) != len(data.permission_ids):
        raise HTTPException(status_code=400, detail="Some permission IDs are invalid")

    set_role_permissions(db, role_id, data.permission_ids)
    return {"message": "Permissions updated"}