"""Roles API v2 - E-ITS roles and permissions management."""
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from uuid import UUID

from app.api.deps import DB
from app.api.v2.auth import CurrentUserV2

router = APIRouter()


class RoleResponse(BaseModel):
    id: str
    role_name: str
    description: str | None


class RoleCreate(BaseModel):
    role_name: str
    description: str | None = None


class RoleUpdate(BaseModel):
    role_name: str | None = None
    description: str | None = None


class PermissionResponse(BaseModel):
    id: str
    code: str
    name: str
    category: str | None


class PermissionAssignment(BaseModel):
    permission_id: str


def check_can_manage_roles(current_user) -> bool:
    """Check if user can manage roles (Infoturbejuht or superadmin)."""
    from app.models.local_user import EITSRole, UserRole
    
    user_roles = current_user.roles if hasattr(current_user, 'roles') else []
    role_names = [r.role_name for r in user_roles] if user_roles else []
    
    # Check local storage for superadmin
    import json
    stored_roles = json.loads(__import__('os').getenv('LOCAL_STORAGE_ROLES', '[]'))
    
    if 'superadmin' in stored_roles or 'admin' in stored_roles:
        return True
    
    return 'Infoturbejuht' in role_names


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
    from uuid import UUID
    from app.models.local_user import EITSRole
    from app.models.e_its_role_permission import EITSRolePermission
    from app.models.permission import Permission
    
    role_uuid = UUID(role_id)
    
    role = db.query(EITSRole).filter(
        EITSRole.id == role_uuid,
        EITSRole.tenant_id == current_user.tenant_id
    ).first()
    
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found"
        )
    
    role_perms = db.query(EITSRolePermission).filter(EITSRolePermission.role_id == role_uuid).all()
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


@router.post("/", response_model=RoleResponse)
def create_role(request: RoleCreate, db: DB, current_user = CurrentUserV2):
    """Create new E-ITS role."""
    from app.models.local_user import EITSRole
    import json
    
    # Check permissions - Infoturbejuht or superadmin
    user_roles = current_user.roles if hasattr(current_user, 'roles') else []
    role_names = [r.role_name for r in user_roles] if user_roles else []
    stored_roles = json.loads(__import__('localStorage') and __import__('os').getenv('LOCAL_STORAGE_ROLES', '[]') or '[]')
    
    if 'Infoturbejuht' not in role_names and 'superadmin' not in stored_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to manage roles"
        )
    
    # Check if role already exists in this tenant
    existing = db.query(EITSRole).filter(
        EITSRole.tenant_id == current_user.tenant_id,
        EITSRole.role_name == request.role_name
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Role already exists in this tenant"
        )
    
    role = EITSRole(
        tenant_id=current_user.tenant_id,
        role_name=request.role_name,
        description=request.description
    )
    db.add(role)
    db.commit()
    db.refresh(role)
    
    return RoleResponse(
        id=str(role.id),
        role_name=role.role_name,
        description=role.description
    )


@router.patch("/{role_id}", response_model=RoleResponse)
def update_role(role_id: str, request: RoleUpdate, db: DB, current_user = CurrentUserV2):
    """Update E-ITS role."""
    from uuid import UUID
    from app.models.local_user import EITSRole
    
    role_uuid = UUID(role_id)
    
    role = db.query(EITSRole).filter(
        EITSRole.id == role_uuid,
        EITSRole.tenant_id == current_user.tenant_id
    ).first()
    
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found"
        )
    
    if request.role_name is not None:
        existing = db.query(EITSRole).filter(
            EITSRole.tenant_id == current_user.tenant_id,
            EITSRole.role_name == request.role_name,
            EITSRole.id != role_uuid
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Role name already exists"
            )
        
        role.role_name = request.role_name
    
    if request.description is not None:
        role.description = request.description
    
    db.commit()
    db.refresh(role)
    
    return RoleResponse(
        id=str(role.id),
        role_name=role.role_name,
        description=role.description
    )


@router.delete("/{role_id}")
def delete_role(role_id: str, db: DB, current_user = CurrentUserV2):
    """Delete E-ITS role."""
    from uuid import UUID
    from app.models.local_user import EITSRole, UserRole
    
    role_uuid = UUID(role_id)
    
    role = db.query(EITSRole).filter(
        EITSRole.id == role_uuid,
        EITSRole.tenant_id == current_user.tenant_id
    ).first()
    
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found"
        )
    
    # Check if role is assigned to any users
    user_count = db.query(UserRole).filter(UserRole.role_id == role_uuid).count()
    if user_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete role: {user_count} users have this role"
        )
    
    db.delete(role)
    db.commit()
    
    return {"message": "Role deleted"}


@router.post("/{role_id}/permissions")
def add_permission_to_role(role_id: str, request: PermissionAssignment, db: DB, current_user = CurrentUserV2):
    """Add permission to role."""
    from uuid import UUID
    from app.models.local_user import EITSRole
    from app.models.e_its_role_permission import EITSRolePermission
    from app.models.permission import Permission
    
    role_uuid = UUID(role_id)
    
    role = db.query(EITSRole).filter(
        EITSRole.id == role_uuid,
        EITSRole.tenant_id == current_user.tenant_id
    ).first()
    
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found"
        )
    
    # Check if permission exists
    perm = db.query(Permission).filter(Permission.id == request.permission_id).first()
    if not perm:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Permission not found"
        )
    
    # Check if already assigned
    existing = db.query(EITSRolePermission).filter(
        EITSRolePermission.role_id == role_uuid,
        EITSRolePermission.permission_id == request.permission_id
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Permission already assigned to role"
        )
    
    rp = EITSRolePermission(role_id=role_uuid, permission_id=request.permission_id)
    db.add(rp)
    db.commit()
    
    return {"message": "Permission added to role"}


@router.delete("/{role_id}/permissions/{permission_id}")
def remove_permission_from_role(role_id: str, permission_id: str, db: DB, current_user = CurrentUserV2):
    """Remove permission from role."""
    from uuid import UUID
    from app.models.local_user import EITSRole
    from app.models.e_its_role_permission import EITSRolePermission
    
    role_uuid = UUID(role_id)
    
    role = db.query(EITSRole).filter(
        EITSRole.id == role_uuid,
        EITSRole.tenant_id == current_user.tenant_id
    ).first()
    
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found"
        )
    
    rp = db.query(EITSRolePermission).filter(
        EITSRolePermission.role_id == role_uuid,
        EITSRolePermission.permission_id == permission_id
    ).first()
    
    if not rp:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Permission not assigned to role"
        )
    
    db.delete(rp)
    db.commit()
    
    return {"message": "Permission removed from role"}