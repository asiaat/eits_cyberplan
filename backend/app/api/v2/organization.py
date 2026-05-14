"""Organization API v2 - People and User Management."""
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session, selectinload

from app.api.deps import DB
from app.api.v2.auth import CurrentUserV2
from app.models.local_user import LocalUser
from app.models.asset import Asset
from app.models.user import User
from app.models.role import Role

router = APIRouter()


class PersonAssetResponse(BaseModel):
    id: str
    name: str
    email: Optional[str] = None
    description: Optional[str] = None
    owner_user_id: Optional[str] = None
    has_user_account: bool = False
    user_roles: List[dict] = []
    person_id: Optional[str] = None
    linked: bool = False


class CreateWorkerRequest(BaseModel):
    person_id: str
    role: Optional[str] = None


def get_tenant_id(current_user: LocalUser, x_tenant_id: Optional[str] = None) -> str:
    if x_tenant_id:
        return x_tenant_id
    return str(current_user.tenant_id)


@router.get("/people", response_model=List[PersonAssetResponse])
def list_people(db: DB, current_user: LocalUser = CurrentUserV2, x_tenant_id: Optional[str] = None):
    """List all person-type assets (people) in the organization."""
    tenant_id = get_tenant_id(current_user, x_tenant_id)

    assets = db.query(Asset).options(
        selectinload(Asset.owner_user),
    ).filter(
        Asset.tenant_id == tenant_id,
        Asset.asset_type == "person"
    ).all()

    results = []
    for asset in assets:
        has_user = bool(asset.owner_user_id)
        user_roles = []
        
        if asset.owner_user_id:
            user = db.query(User).filter(User.id == asset.owner_user_id).first()
            if user and hasattr(user, 'roles') and user.roles:
                user_roles = [{"id": str(r.id), "code": r.code, "name": r.name} for r in user.roles]

        results.append(PersonAssetResponse(
            id=str(asset.id),
            name=asset.name,
            email=asset.email,
            description=asset.description,
            owner_user_id=asset.owner_user_id,
            has_user_account=has_user,
            user_roles=user_roles,
            person_id=str(asset.person_id) if asset.person_id else None,
            linked=True
        ))

    return results


@router.get("/people/available", response_model=List[dict])
def list_available_people(db: DB, current_user: LocalUser = CurrentUserV2, x_tenant_id: Optional[str] = None):
    """List persons not yet workers in the organization."""
    from app.models.person import Person, PersonOrganization
    
    tenant_id = get_tenant_id(current_user, x_tenant_id)

    linked_person_ids = db.query(PersonOrganization.person_id).filter(
        PersonOrganization.tenant_id == tenant_id
    ).all()
    linked_ids = [p.person_id for p in linked_person_ids]

    asset_person_ids = db.query(Asset.person_id).filter(
        Asset.tenant_id == tenant_id,
        Asset.asset_type == "person",
        Asset.person_id.isnot(None)
    ).all()
    asset_person_ids = [a.person_id for a in asset_person_ids if a.person_id]

    all_excluded = set(linked_ids + asset_person_ids)

    from app.models.person import Person
    query = db.query(Person).order_by(Person.last_name, Person.first_name)
    
    if all_excluded:
        query = query.filter(Person.id.notin_(all_excluded))
    
    persons = query.all()

    return [
        {
            "id": str(p.id),
            "name": p.name,
            "national_id": p.national_id,
            "email": p.email,
            "phone": p.phone
        }
        for p in persons
    ]


@router.post("/people", status_code=status.HTTP_201_CREATED)
def create_worker(db: DB, request: CreateWorkerRequest, current_user: LocalUser = CurrentUserV2, x_tenant_id: Optional[str] = None):
    """Create a worker by linking existing Person to organization."""
    from app.models.person import Person, PersonOrganization
    
    tenant_id = get_tenant_id(current_user, x_tenant_id)

    person = db.query(Person).filter(Person.id == request.person_id).first()
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")

    existing_link = db.query(PersonOrganization).filter(
        PersonOrganization.person_id == person.id,
        PersonOrganization.tenant_id == tenant_id
    ).first()

    if not existing_link:
        link = PersonOrganization(
            person_id=person.id,
            tenant_id=tenant_id,
            role=request.role
        )
        db.add(link)

    existing_asset = db.query(Asset).filter(
        Asset.person_id == person.id,
        Asset.tenant_id == tenant_id,
        Asset.asset_type == "person"
    ).first()

    if not existing_asset:
        asset = Asset(
            name=person.name,
            email=person.email,
            description=request.role,
            tenant_id=tenant_id,
            asset_type="person",
            person_id=person.id,
            status="active"
        )
        db.add(asset)
        db.commit()
        db.refresh(asset)
    else:
        if request.role:
            existing_asset.description = request.role
            db.commit()
        asset = existing_asset

    return {
        "id": str(asset.id),
        "name": asset.name,
        "email": asset.email,
        "description": asset.description,
        "person_id": str(person.id),
        "linked": True
    }


@router.delete("/people/{asset_id}", status_code=status.HTTP_204_NO_CONTENT)
def unlink_worker(asset_id: UUID, db: DB, current_user: LocalUser = CurrentUserV2, x_tenant_id: Optional[str] = None):
    """Delete/unlink a worker."""
    tenant_id = get_tenant_id(current_user, x_tenant_id)

    asset = db.query(Asset).filter(
        Asset.id == asset_id,
        Asset.tenant_id == tenant_id
    ).first()

    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    if asset.person_id:
        db.query(PersonOrganization).filter(
            PersonOrganization.person_id == asset.person_id,
            PersonOrganization.tenant_id == tenant_id
        ).delete()

    db.delete(asset)
    db.commit()


@router.post("/people/{asset_id}/create-user", status_code=status.HTTP_201_CREATED)
def create_user_from_worker(asset_id: UUID, db: DB, request: CreateWorkerRequest, current_user: LocalUser = CurrentUserV2, x_tenant_id: Optional[str] = None):
    """Create user from person asset."""
    from app.models.person import Person
    from app.core.security import get_password_hash
    
    tenant_id = get_tenant_id(current_user, x_tenant_id)

    asset = db.query(Asset).filter(
        Asset.id == asset_id,
        Asset.tenant_id == tenant_id
    ).first()

    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    if not asset.person_id:
        raise HTTPException(status_code=400, detail="Asset has no linked person")

    person = db.query(Person).filter(Person.id == asset.person_id).first()
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")

    if not person.email:
        raise HTTPException(status_code=400, detail="Person has no email")

    existing_user = db.query(User).filter(User.email == person.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="User with this email already exists")

    password = request.role or "changeme123"
    
    user = User(
        email=person.email,
        full_name=person.name,
        password_hash=get_password_hash(password),
        tenant_id=tenant_id,
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    asset.owner_user_id = str(user.id)
    db.commit()

    return {
        "id": str(user.id),
        "email": user.email,
        "full_name": user.full_name
    }