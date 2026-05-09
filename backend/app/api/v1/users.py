"""Users API endpoints."""
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.api.deps import DB, CurrentUser

router = APIRouter()


class UserCreate(BaseModel):
    email: str
    name: str
    password: str


class UserUpdate(BaseModel):
    email: str | None = None
    name: str | None = None
    is_active: bool | None = None


class UserResponse(BaseModel):
    id: UUID
    email: str
    name: str
    is_active: bool
    roles: list = []

    model_config = {"from_attributes": True}


@router.get("/", response_model=List[UserResponse])
def list_users(db: DB, current_user: CurrentUser):
    """List all users (admin only)."""
    from app.models.user import User
    from app.core.permissions import get_user_roles
    
    users = db.query(User).all()
    
    result = []
    for user in users:
        roles = get_user_roles(db, user)
        result.append({
            "id": str(user.id),
            "email": user.email,
            "name": user.name,
            "is_active": user.is_active,
            "roles": roles,
        })
    
    return result


@router.post("/", response_model=UserResponse)
def create_user(user_in: UserCreate, db: DB, current_user: CurrentUser):
    """Create a new user with default auditor role."""
    from app.core.security import get_password_hash
    from app.models.user import User
    from app.models.membership import Membership
    from app.models.role import Role

    user = User(
        email=user_in.email,
        name=user_in.name,
        hashed_password=get_password_hash(user_in.password),
    )
    db.add(user)
    db.flush()

    auditor_role = db.query(Role).filter(Role.code == "auditor").first()
    if auditor_role:
        membership = Membership(user_id=user.id, role_id=auditor_role.id)
        db.add(membership)

    db.commit()
    db.refresh(user)
    return user


@router.get("/{user_id}", response_model=UserResponse)
def get_user(user_id: str, db: DB, current_user: CurrentUser):
    """Get a user by ID."""
    from app.models.user import User

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.patch("/{user_id}", response_model=UserResponse)
def update_user(user_id: str, user_in: UserUpdate, db: DB, current_user: CurrentUser):
    """Update a user."""
    from app.models.user import User

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="User not found")
    if user_in.email is not None:
        user.email = user_in.email
    if user_in.name is not None:
        user.name = user_in.name
    if user_in.is_active is not None:
        user.is_active = user_in.is_active
    db.commit()
    db.refresh(user)
    return user


@router.get("/{user_id}/roles")
def get_user_roles(user_id: str, db: DB, current_user: CurrentUser):
    """Get roles assigned to a user."""
    from app.models.membership import Membership
    from app.models.role import Role
    from app.core.permissions import get_user_roles as get_user_roles_helper
    from uuid import UUID

    user = db.query(User).filter(User.id == UUID(user_id)).first()
    if not user:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="User not found")

    return get_user_roles_helper(db, user)


@router.post("/{user_id}/roles")
def assign_user_role(user_id: str, data: dict, db: DB, current_user: CurrentUser):
    """Assign a role to a user."""
    from app.models.membership import Membership
    from app.models.role import Role
    from uuid import UUID

    user = db.query(User).filter(User.id == UUID(user_id)).first()
    if not user:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="User not found")

    role_id = data.get("role_id")
    if not role_id:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="role_id is required")

    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Role not found")

    # Check if already assigned
    existing = db.query(Membership).filter(
        Membership.user_id == UUID(user_id),
        Membership.role_id == role_id
    ).first()

    if existing:
        return {"message": "Role already assigned"}

    # Get or create default tenant
    from app.models.tenant import Tenant
    tenant = db.query(Tenant).first()
    if not tenant:
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail="No tenant found")

    membership = Membership(
        tenant_id=tenant.id,
        user_id=UUID(user_id),
        role_id=role_id
    )
    db.add(membership)
    db.commit()
    return {"message": "Role assigned"}


@router.delete("/{user_id}/roles/{role_id}")
def remove_user_role(user_id: str, role_id: str, db: DB, current_user: CurrentUser):
    """Remove a role from a user."""
    from app.models.membership import Membership
    from uuid import UUID

    membership = db.query(Membership).filter(
        Membership.user_id == UUID(user_id),
        Membership.role_id == role_id
    ).first()

    if not membership:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Role not assigned to user")

    db.delete(membership)
    db.commit()
    return {"message": "Role removed"}