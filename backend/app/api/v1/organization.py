"""Organization API endpoints - People and User Management."""
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import DB, CurrentUser
from app.models.user import User
from app.models.asset import Asset
from app.models.membership import Membership
from app.models.role import Role
from app.core.security import get_password_hash

router = APIRouter()


class PersonAssetResponse(BaseModel):
    id: str
    name: str
    email: Optional[str] = None
    description: Optional[str] = None
    owner_user_id: Optional[str] = None
    has_user_account: bool = False
    user_roles: List[dict] = []

    model_config = {"from_attributes": True}


class CreateUserFromAssetRequest(BaseModel):
    password: str
    email: Optional[str] = None


class CreatePersonAssetRequest(BaseModel):
    name: str
    email: Optional[str] = None
    description: Optional[str] = None


class LinkUserToAssetRequest(BaseModel):
    user_id: str


class UserWithRolesResponse(BaseModel):
    id: str
    email: str
    name: str
    is_active: bool
    roles: List[dict] = []
    linked_asset_id: Optional[str] = None

    model_config = {"from_attributes": True}


@router.get("/people", response_model=List[PersonAssetResponse])
def list_people(db: DB, current_user: CurrentUser, include_all: bool = False):
    """
    List all person-type assets (people) in the organization.
    Optionally include non-person assets if include_all=true.
    """
    query = db.query(Asset)
    if not include_all:
        query = query.filter(Asset.asset_type == "person")
    
    assets = query.order_by(Asset.name).all()
    
    result = []
    for asset in assets:
        user_roles = []
        has_user = False
        
        if asset.owner_user_id:
            user = db.query(User).filter(User.id == asset.owner_user_id).first()
            if user:
                has_user = True
                memberships = db.query(Membership).filter(Membership.user_id == user.id).all()
                for m in memberships:
                    role = db.query(Role).filter(Role.id == m.role_id).first()
                    if role:
                        user_roles.append({"id": role.id, "code": role.code, "name": role.name, "is_default": role.is_default})
        
        result.append(PersonAssetResponse(
            id=str(asset.id),
            name=asset.name,
            email=asset.description,  # Using description for email
            description=asset.description,
            owner_user_id=str(asset.owner_user_id) if asset.owner_user_id else None,
            has_user_account=has_user,
            user_roles=user_roles
        ))
    
    return result


@router.post("/people", response_model=PersonAssetResponse)
def create_person(db: DB, current_user: CurrentUser, data: CreatePersonAssetRequest):
    """Create a new person asset."""
    from uuid import uuid4
    
    # Get tenant from user
    membership = db.query(Membership).filter(Membership.user_id == current_user.id).first()
    if not membership:
        raise HTTPException(status_code=400, detail="No tenant found for user")
    
    asset = Asset(
        id=uuid4(),
        tenant_id=membership.tenant_id,
        name=data.name,
        asset_type="person",
        description=data.email,  # Store email in description
    )
    db.add(asset)
    db.commit()
    db.refresh(asset)
    
    return PersonAssetResponse(
        id=str(asset.id),
        name=asset.name,
        email=data.email,
        description=asset.description,
        has_user_account=False,
        user_roles=[]
    )


@router.post("/people/{asset_id}/create-user", response_model=UserWithRolesResponse)
def create_user_from_person(db: DB, current_user: CurrentUser, asset_id: str, data: CreateUserFromAssetRequest):
    """Create a CyberPlan user from a person asset."""
    from uuid import uuid4
    
    asset = db.query(Asset).filter(Asset.id == UUID(asset_id)).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Person asset not found")
    
    if asset.asset_type != "person":
        raise HTTPException(status_code=400, detail="Asset is not a person type")
    
    if asset.owner_user_id:
        raise HTTPException(status_code=400, detail="Person already has a user account")
    
    # Determine email - use provided or from asset
    email = data.email or asset.description
    if not email:
        raise HTTPException(status_code=400, detail="Email is required")
    
    # Check if email already exists
    existing = db.query(User).filter(User.email == email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already in use")
    
    # Get tenant
    membership = db.query(Membership).filter(Membership.user_id == current_user.id).first()
    
    # Create user
    user = User(
        id=uuid4(),
        email=email,
        name=asset.name,
        hashed_password=get_password_hash(data.password),
        is_active=True
    )
    db.add(user)
    
    # Link asset to user
    asset.owner_user_id = user.id
    
    db.commit()
    db.refresh(user)
    db.refresh(asset)
    
    return UserWithRolesResponse(
        id=str(user.id),
        email=user.email,
        name=user.name,
        is_active=user.is_active,
        roles=[],
        linked_asset_id=str(asset.id)
    )


@router.get("/users", response_model=List[UserWithRolesResponse])
def list_organization_users(db: DB, current_user: CurrentUser, with_asset_only: bool = False):
    """List all CyberPlan users in the organization."""
    users = db.query(User).order_by(User.name).all()
    
    if with_asset_only:
        # Filter to only users who are linked to an asset
        users = [u for u in users if u.owned_assets]
    
    result = []
    for user in users:
        memberships = db.query(Membership).filter(Membership.user_id == user.id).all()
        roles = []
        for m in memberships:
            role = db.query(Role).filter(Role.id == m.role_id).first()
            if role:
                roles.append({"id": role.id, "code": role.code, "name": role.name, "is_default": role.is_default})
        
        # Find linked asset
        linked_asset = None
        owned_assets = db.query(Asset).filter(Asset.owner_user_id == user.id, Asset.asset_type == "person").first()
        if owned_assets:
            linked_asset = str(owned_assets.id)
        
        result.append(UserWithRolesResponse(
            id=str(user.id),
            email=user.email,
            name=user.name,
            is_active=user.is_active,
            roles=roles,
            linked_asset_id=linked_asset
        ))
    
    return result


@router.post("/users", response_model=UserWithRolesResponse)
def create_organization_user(db: DB, current_user: CurrentUser, data: dict):
    """Create a new CyberPlan user (optionally linked to an asset)."""
    from uuid import uuid4
    
    name = data.get("name")
    email = data.get("email")
    password = data.get("password")
    linked_asset_id = data.get("linked_asset_id")
    
    if not name or not email or not password:
        raise HTTPException(status_code=400, detail="name, email, and password are required")
    
    # Check if email exists
    existing = db.query(User).filter(User.email == email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already in use")
    
    # Get tenant
    membership = db.query(Membership).filter(Membership.user_id == current_user.id).first()
    
    # Create user
    user = User(
        id=uuid4(),
        email=email,
        name=name,
        hashed_password=get_password_hash(password),
        is_active=True
    )
    db.add(user)
    
    # Link to asset if provided
    if linked_asset_id:
        asset = db.query(Asset).filter(Asset.id == UUID(linked_asset_id)).first()
        if asset:
            asset.owner_user_id = user.id
    
    db.commit()
    db.refresh(user)
    
    return UserWithRolesResponse(
        id=str(user.id),
        email=user.email,
        name=user.name,
        is_active=user.is_active,
        roles=[],
        linked_asset_id=linked_asset_id
    )


@router.post("/users/{user_id}/assign-role")
def assign_role_to_user(db: DB, current_user: CurrentUser, user_id: str, data: dict):
    """Assign a role to a user."""
    role_id = data.get("role_id")
    if not role_id:
        raise HTTPException(status_code=400, detail="role_id is required")
    
    user = db.query(User).filter(User.id == UUID(user_id)).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    
    # Check if already assigned
    existing = db.query(Membership).filter(
        Membership.user_id == UUID(user_id),
        Membership.role_id == role_id
    ).first()
    
    if existing:
        return {"message": "Role already assigned"}
    
    # Get or create tenant
    membership = db.query(Membership).filter(Membership.user_id == current_user.id).first()
    if not membership:
        raise HTTPException(status_code=500, detail="No tenant found")
    
    new_membership = Membership(
        tenant_id=membership.tenant_id,
        user_id=user.id,
        role_id=role_id
    )
    db.add(new_membership)
    db.commit()
    
    return {"message": "Role assigned"}


@router.delete("/users/{user_id}/remove-role/{role_id}")
def remove_role_from_user(db: DB, current_user: CurrentUser, user_id: str, role_id: str):
    """Remove a role from a user."""
    membership = db.query(Membership).filter(
        Membership.user_id == UUID(user_id),
        Membership.role_id == role_id
    ).first()
    
    if not membership:
        raise HTTPException(status_code=404, detail="Role not assigned to user")
    
    db.delete(membership)
    db.commit()
    
    return {"message": "Role removed"}


@router.delete("/users/{user_id}")
def delete_organization_user(db: DB, current_user: CurrentUser, user_id: str):
    """Delete a user."""
    user = db.query(User).filter(User.id == UUID(user_id)).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")
    
    # Remove from assets
    assets = db.query(Asset).filter(Asset.owner_user_id == user.id).all()
    for asset in assets:
        asset.owner_user_id = None
    
    # Remove memberships
    db.query(Membership).filter(Membership.user_id == user.id).delete()
    
    # Delete user
    db.delete(user)
    db.commit()
    
    return {"message": "User deleted"}


@router.patch("/users/{user_id}/activate")
def activate_user(db: DB, current_user: CurrentUser, user_id: str):
    """Activate a user."""
    user = db.query(User).filter(User.id == UUID(user_id)).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.is_active = True
    db.commit()
    
    return {"message": "User activated"}


@router.patch("/users/{user_id}/deactivate")
def deactivate_user(db: DB, current_user: CurrentUser, user_id: str):
    """Deactivate a user."""
    user = db.query(User).filter(User.id == UUID(user_id)).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot deactivate yourself")
    
    user.is_active = False
    db.commit()
    
    return {"message": "User deactivated"}


@router.get("/users/{user_id}")
def get_organization_user(db: DB, current_user: CurrentUser, user_id: str):
    """Get a specific user with roles and linked asset."""
    user = db.query(User).filter(User.id == UUID(user_id)).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    memberships = db.query(Membership).filter(Membership.user_id == user.id).all()
    roles = []
    for m in memberships:
        role = db.query(Role).filter(Role.id == m.role_id).first()
        if role:
            roles.append({"id": role.id, "code": role.code, "name": role.name, "is_default": role.is_default})
    
    linked_asset = None
    owned_assets = db.query(Asset).filter(Asset.owner_user_id == user.id, Asset.asset_type == "person").first()
    if owned_assets:
        linked_asset = {"id": str(owned_assets.id), "name": owned_assets.name}
    
    return {
        "id": str(user.id),
        "email": user.email,
        "name": user.name,
        "is_active": user.is_active,
        "roles": roles,
        "linked_asset": linked_asset
    }