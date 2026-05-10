"""Persons API endpoints - Global People Directory."""
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import DB, CurrentUser
from app.models.user import User
from app.models.membership import Membership
from app.models.person import Person, PersonOrganization
from app.models.tenant import Tenant
from app.models.asset import Asset
from app.models.role import Role

router = APIRouter()


class PersonResponse(BaseModel):
    id: str
    name: str
    email: Optional[str] = None
    position: Optional[str] = None
    phone: Optional[str] = None
    notes: Optional[str] = None
    organizations: List[dict] = []
    has_user_account: bool = False
    user_roles: List[dict] = []

    model_config = {"from_attributes": True}


class PersonCreate(BaseModel):
    name: str
    email: Optional[str] = None
    position: Optional[str] = None
    phone: Optional[str] = None
    notes: Optional[str] = None


class PersonUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    position: Optional[str] = None
    phone: Optional[str] = None
    notes: Optional[str] = None


class OrganizationLinkCreate(BaseModel):
    tenant_id: str
    role: Optional[str] = None


def get_user_roles(db: Session, user: User) -> List[dict]:
    memberships = db.query(Membership).filter(Membership.user_id == user.id).all()
    roles = []
    for m in memberships:
        role = db.query(Role).filter(Role.id == m.role_id).first()
        if role:
            roles.append({"id": role.id, "code": role.code, "name": role.name, "is_default": role.is_default})
    return roles


def is_admin_or_ism(db: DB, current_user: CurrentUser) -> bool:
    membership = db.query(Membership).filter(Membership.user_id == current_user.id).first()
    if not membership:
        return False
    role = db.query(Role).filter(Role.id == membership.role_id).first()
    if not role:
        return False
    return role.code in ["admin", "ism"]


@router.get("/", response_model=List[PersonResponse])
def list_persons(db: DB, current_user: CurrentUser, search: Optional[str] = None):
    """List all persons in the global directory."""
    query = db.query(Person).order_by(Person.name)
    
    if search:
        query = query.filter(Person.name.ilike(f"%{search}%"))
    
    persons = query.all()
    
    result = []
    for person in persons:
        org_links = db.query(PersonOrganization).filter(PersonOrganization.person_id == person.id).all()
        orgs = []
        for link in org_links:
            tenant = db.query(Tenant).filter(Tenant.id == link.tenant_id).first()
            if tenant:
                orgs.append({"tenant_id": str(link.tenant_id), "tenant_name": tenant.name, "role": link.role})
        
        has_user = False
        user_roles = []
        asset = db.query(Asset).filter(Asset.person_id == person.id).first()
        if asset and asset.owner_user_id:
            user = db.query(User).filter(User.id == asset.owner_user_id).first()
            if user:
                has_user = True
                user_roles = get_user_roles(db, user)
        
        result.append(PersonResponse(
            id=str(person.id),
            name=person.name,
            email=person.email,
            position=person.position,
            phone=person.phone,
            notes=person.notes,
            organizations=orgs,
            has_user_account=has_user,
            user_roles=user_roles
        ))
    
    return result


@router.post("/", response_model=PersonResponse)
def create_person(db: DB, current_user: CurrentUser, data: PersonCreate):
    """Create a new person in the global directory."""
    if not is_admin_or_ism(db, current_user):
        raise HTTPException(status_code=403, detail="Only admins and ISM can manage persons")
    
    from uuid import uuid4
    person = Person(
        id=uuid4(),
        name=data.name,
        email=data.email,
        position=data.position,
        phone=data.phone,
        notes=data.notes
    )
    db.add(person)
    db.commit()
    db.refresh(person)
    
    return PersonResponse(
        id=str(person.id),
        name=person.name,
        email=person.email,
        position=person.position,
        phone=person.phone,
        notes=person.notes,
        organizations=[],
        has_user_account=False,
        user_roles=[]
    )


@router.get("/{person_id}", response_model=PersonResponse)
def get_person(db: DB, current_user: CurrentUser, person_id: str):
    """Get a specific person."""
    person = db.query(Person).filter(Person.id == UUID(person_id)).first()
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")
    
    org_links = db.query(PersonOrganization).filter(PersonOrganization.person_id == person.id).all()
    orgs = []
    for link in org_links:
        tenant = db.query(Tenant).filter(Tenant.id == link.tenant_id).first()
        if tenant:
            orgs.append({"tenant_id": str(link.tenant_id), "tenant_name": tenant.name, "role": link.role})
    
    has_user = False
    user_roles = []
    asset = db.query(Asset).filter(Asset.person_id == person.id).first()
    if asset and asset.owner_user_id:
        user = db.query(User).filter(User.id == asset.owner_user_id).first()
        if user:
            has_user = True
            user_roles = get_user_roles(db, user)
    
    return PersonResponse(
        id=str(person.id),
        name=person.name,
        email=person.email,
        position=person.position,
        phone=person.phone,
        notes=person.notes,
        organizations=orgs,
        has_user_account=has_user,
        user_roles=user_roles
    )


@router.patch("/{person_id}", response_model=PersonResponse)
def update_person(db: DB, current_user: CurrentUser, person_id: str, data: PersonUpdate):
    """Update a person."""
    if not is_admin_or_ism(db, current_user):
        raise HTTPException(status_code=403, detail="Only admins and ISM can manage persons")
    
    person = db.query(Person).filter(Person.id == UUID(person_id)).first()
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")
    
    if data.name is not None:
        person.name = data.name
    if data.email is not None:
        person.email = data.email
    if data.position is not None:
        person.position = data.position
    if data.phone is not None:
        person.phone = data.phone
    if data.notes is not None:
        person.notes = data.notes
    
    db.commit()
    db.refresh(person)
    
    org_links = db.query(PersonOrganization).filter(PersonOrganization.person_id == person.id).all()
    orgs = []
    for link in org_links:
        tenant = db.query(Tenant).filter(Tenant.id == link.tenant_id).first()
        if tenant:
            orgs.append({"tenant_id": str(link.tenant_id), "tenant_name": tenant.name, "role": link.role})
    
    has_user = False
    user_roles = []
    asset = db.query(Asset).filter(Asset.person_id == person.id).first()
    if asset and asset.owner_user_id:
        user = db.query(User).filter(User.id == asset.owner_user_id).first()
        if user:
            has_user = True
            user_roles = get_user_roles(db, user)
    
    return PersonResponse(
        id=str(person.id),
        name=person.name,
        email=person.email,
        position=person.position,
        phone=person.phone,
        notes=person.notes,
        organizations=orgs,
        has_user_account=has_user,
        user_roles=user_roles
    )


@router.delete("/{person_id}")
def delete_person(db: DB, current_user: CurrentUser, person_id: str):
    """Delete a person."""
    if not is_admin_or_ism(db, current_user):
        raise HTTPException(status_code=403, detail="Only admins and ISM can manage persons")
    
    person = db.query(Person).filter(Person.id == UUID(person_id)).first()
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")
    
    db.query(PersonOrganization).filter(PersonOrganization.person_id == person.id).delete()
    db.query(Asset).filter(Asset.person_id == person.id).delete()
    db.delete(person)
    db.commit()
    
    return {"message": "Person deleted"}


@router.get("/{person_id}/organizations", response_model=List[dict])
def get_person_organizations(db: DB, current_user: CurrentUser, person_id: str):
    """Get organizations a person is linked to."""
    person = db.query(Person).filter(Person.id == UUID(person_id)).first()
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")
    
    org_links = db.query(PersonOrganization).filter(PersonOrganization.person_id == person.id).all()
    result = []
    for link in org_links:
        tenant = db.query(Tenant).filter(Tenant.id == link.tenant_id).first()
        if tenant:
            result.append({"tenant_id": str(link.tenant_id), "tenant_name": tenant.name, "role": link.role})
    
    return result


@router.post("/{person_id}/organizations", response_model=dict)
def link_person_to_organization(db: DB, current_user: CurrentUser, person_id: str, data: OrganizationLinkCreate):
    """Link a person to an organization."""
    if not is_admin_or_ism(db, current_user):
        raise HTTPException(status_code=403, detail="Only admins and ISM can manage persons")
    
    person = db.query(Person).filter(Person.id == UUID(person_id)).first()
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")
    
    tenant = db.query(Tenant).filter(Tenant.id == UUID(data.tenant_id)).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    existing = db.query(PersonOrganization).filter(
        PersonOrganization.person_id == person.id,
        PersonOrganization.tenant_id == UUID(data.tenant_id)
    ).first()
    
    if existing:
        existing.role = data.role
        db.commit()
    else:
        from uuid import uuid4
        link = PersonOrganization(
            id=uuid4(),
            person_id=person.id,
            tenant_id=UUID(data.tenant_id),
            role=data.role
        )
        db.add(link)
        db.commit()
    
    return {"message": "Person linked to organization", "tenant_id": data.tenant_id, "role": data.role}


@router.delete("/{person_id}/organizations/{tenant_id}")
def unlink_person_from_organization(db: DB, current_user: CurrentUser, person_id: str, tenant_id: str):
    """Unlink a person from an organization."""
    if not is_admin_or_ism(db, current_user):
        raise HTTPException(status_code=403, detail="Only admins and ISM can manage persons")
    
    link = db.query(PersonOrganization).filter(
        PersonOrganization.person_id == UUID(person_id),
        PersonOrganization.tenant_id == UUID(tenant_id)
    ).first()
    
    if not link:
        raise HTTPException(status_code=404, detail="Link not found")
    
    db.delete(link)
    db.commit()
    
    return {"message": "Person unlinked from organization"}


@router.get("/organizations/{tenant_id}", response_model=List[PersonResponse])
def list_persons_by_organization(db: DB, current_user: CurrentUser, tenant_id: str):
    """List all persons linked to a specific organization."""
    org_links = db.query(PersonOrganization).filter(PersonOrganization.tenant_id == UUID(tenant_id)).all()
    person_ids = [link.person_id for link in org_links]
    
    if not person_ids:
        return []
    
    persons = db.query(Person).filter(Person.id.in_(person_ids)).order_by(Person.name).all()
    
    result = []
    for person in persons:
        link = next((l for l in org_links if l.person_id == person.id), None)
        
        has_user = False
        user_roles = []
        asset = db.query(Asset).filter(Asset.person_id == person.id).first()
        if asset and asset.owner_user_id:
            user = db.query(User).filter(User.id == asset.owner_user_id).first()
            if user:
                has_user = True
                user_roles = get_user_roles(db, user)
        
        result.append(PersonResponse(
            id=str(person.id),
            name=person.name,
            email=person.email,
            position=person.position,
            phone=person.phone,
            notes=person.notes,
            organizations=[{"tenant_id": tenant_id, "tenant_name": "", "role": link.role if link else None}],
            has_user_account=has_user,
            user_roles=user_roles
        ))
    
    return result