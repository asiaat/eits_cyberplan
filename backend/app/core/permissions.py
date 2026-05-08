"""Permission check utilities."""
from typing import List
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.role import Role
from app.models.permission import Permission
from app.models.membership import Membership


def get_user_permissions(db: Session, user: User) -> List[str]:
    """Get all permission codes for a user based on their roles."""
    if not user or not user.is_active:
        return []

    # Get user's roles via memberships
    memberships = db.query(Membership).filter(Membership.user_id == user.id).all()
    role_ids = [m.role_id for m in memberships]

    if not role_ids:
        return []

    # Get all permissions for these roles
    from app.models.role_permission import RolePermission
    role_perms = db.query(RolePermission).filter(RolePermission.role_id.in_(role_ids)).all()
    perm_ids = [rp.permission_id for rp in role_perms]

    permissions = db.query(Permission).filter(Permission.id.in_(perm_ids)).all()
    return [p.code for p in permissions]


def has_permission(db: Session, user: User, permission_code: str) -> bool:
    """Check if user has a specific permission."""
    if not user or not user.is_active:
        return False

    # Admin always has all permissions
    memberships = db.query(Membership).filter(Membership.user_id == user.id).all()
    role_ids = [m.role_id for m in memberships]

    admin_role = db.query(Role).filter(Role.code == "admin").first()
    if admin_role and admin_role.id in role_ids:
        return True

    # Check specific permission
    from app.models.role_permission import RolePermission
    role_perms = db.query(RolePermission).filter(RolePermission.role_id.in_(role_ids)).all()
    perm_ids = [rp.permission_id for rp in role_perms]

    perm = db.query(Permission).filter(
        Permission.code == permission_code,
        Permission.id.in_(perm_ids)
    ).first()

    return perm is not None


def get_user_roles(db: Session, user: User) -> List[dict]:
    """Get all roles for a user."""
    if not user:
        return []

    memberships = db.query(Membership).filter(Membership.user_id == user.id).all()
    roles = []
    for m in memberships:
        role = db.query(Role).filter(Role.id == m.role_id).first()
        if role:
            roles.append({
                "id": role.id,
                "code": role.code,
                "name": role.name,
            })
    return roles


def get_role_permissions(db: Session, role_id: str) -> List[dict]:
    """Get all permissions for a role."""
    from app.models.role_permission import RolePermission
    role_perms = db.query(RolePermission).filter(RolePermission.role_id == role_id).all()
    perm_ids = [rp.permission_id for rp in role_perms]

    permissions = db.query(Permission).filter(Permission.id.in_(perm_ids)).all()
    return [
        {"id": p.id, "code": p.code, "name": p.name, "category": p.category}
        for p in permissions
    ]


def set_role_permissions(db: Session, role_id: str, permission_ids: List[str]) -> None:
    """Set permissions for a role (replace existing)."""
    from app.models.role_permission import RolePermission

    # Remove existing
    db.query(RolePermission).filter(RolePermission.role_id == role_id).delete()

    # Add new
    for perm_id in permission_ids:
        rp = RolePermission(role_id=role_id, permission_id=perm_id)
        db.add(rp)

    db.commit()