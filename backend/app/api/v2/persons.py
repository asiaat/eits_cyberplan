"""Persons API v2 - Tenant-scoped People Directory."""
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session, selectinload

from app.api.deps import DB
from app.api.v2.auth import CurrentUserV2
from app.models.local_user import LocalUser
from app.models.membership import Membership
from app.models.person import Person, PersonOrganization
from app.models.tenant import Tenant
from app.models.asset import Asset
from app.models.user import User

router = APIRouter()


class PersonResponse(BaseModel):
    id: str
    national_id: Optional[str] = None
    first_name: str
    last_name: str
    name: str
    date_of_birth: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    additional_info: Optional[str] = None
    organizations: List[dict] = []
    has_user_account: bool = False
    user_roles: List[dict] = []
    linked_org_ids: List[str] = []


class PersonCreate(BaseModel):
    national_id: Optional[str] = None
    first_name: str
    last_name: str
    date_of_birth: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    additional_info: Optional[str] = None


class PersonUpdate(BaseModel):
    national_id: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    date_of_birth: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    additional_info: Optional[str] = None


class OrganizationLinkCreate(BaseModel):
    role: Optional[str] = None


def get_tenant_id(current_user: LocalUser, x_tenant_id: Optional[str] = None) -> str:
    if x_tenant_id:
        return x_tenant_id
    return str(current_user.tenant_id)


@router.get("/", response_model=List[PersonResponse])
def list_persons(db: DB, current_user: LocalUser = CurrentUserV2, search: Optional[str] = None, x_tenant_id: Optional[str] = None):
    """List all persons in the current tenant."""
    tenant_id = get_tenant_id(current_user, x_tenant_id)

    query = db.query(Person).order_by(Person.last_name, Person.first_name)

    if search:
        search_filter = f"%{search}%"
        query = query.filter(
            (Person.first_name.ilike(search_filter)) |
            (Person.last_name.ilike(search_filter)) |
            (Person.national_id.ilike(search_filter)) |
            (Person.email.ilike(search_filter))
        )

    persons = query.all()
    if not persons:
        return []

    person_ids = [p.id for p in persons]

    person_org_links = db.query(PersonOrganization).filter(
        PersonOrganization.person_id.in_(person_ids),
        PersonOrganization.tenant_id == tenant_id
    ).all() if person_ids else []

    org_ids = {link.tenant_id for link in person_org_links}
    tenants = {t.id: t for t in db.query(Tenant).filter(Tenant.id.in_(org_ids)).all()} if org_ids else {}

    links_by_person = {}
    for link in person_org_links:
        links_by_person.setdefault(link.person_id, []).append(link)

    linked_org_ids_by_person = {}
    for link in person_org_links:
        linked_org_ids_by_person.setdefault(link.person_id, set()).add(str(link.tenant_id))

    assets = db.query(Asset).filter(
        Asset.person_id.in_(person_ids),
        Asset.tenant_id == tenant_id
    ).all() if person_ids else []

    asset_by_person = {a.person_id: a for a in assets if a.person_id}
    person_user_ids = [a.owner_user_id for a in assets if a.owner_user_id]
    users = {u.id: u for u in db.query(User).filter(User.id.in_(person_user_ids)).all()} if person_user_ids else {}

    results = []
    for person in persons:
        orgs = links_by_person.get(person.id, [])
        org_list = []
        for link in orgs:
            tenant = tenants.get(link.tenant_id)
            org_list.append({
                "tenant_id": str(link.tenant_id),
                "tenant_name": tenant.name if tenant else "Unknown",
                "role": link.role
            })

        asset = asset_by_person.get(person.id)
        has_user = bool(asset and asset.owner_user_id and asset.owner_user_id in users)
        user_roles = []

        if asset and asset.owner_user_id:
            user = users.get(asset.owner_user_id)
            if user and hasattr(user, 'roles') and user.roles:
                user_roles = [{"id": str(r.id), "code": r.code, "name": r.name} for r in user.roles]

        results.append(PersonResponse(
            id=str(person.id),
            national_id=person.national_id,
            first_name=person.first_name,
            last_name=person.last_name,
            name=person.name,
            date_of_birth=str(person.date_of_birth) if person.date_of_birth else None,
            email=person.email,
            phone=person.phone,
            additional_info=person.additional_info,
            organizations=org_list,
            has_user_account=has_user,
            user_roles=user_roles,
            linked_org_ids=list(linked_org_ids_by_person.get(person.id, set()))
        ))

    return results


@router.post("/", response_model=PersonResponse, status_code=status.HTTP_201_CREATED)
def create_person(db: DB, request: PersonCreate, current_user: LocalUser = CurrentUserV2, x_tenant_id: Optional[str] = None):
    """Create a new person."""
    tenant_id = get_tenant_id(current_user, x_tenant_id)

    person = Person(
        national_id=request.national_id,
        first_name=request.first_name,
        last_name=request.last_name,
        date_of_birth=request.date_of_birth,
        email=request.email,
        phone=request.phone,
        additional_info=request.additional_info
    )
    db.add(person)
    db.commit()
    db.refresh(person)

    return PersonResponse(
        id=str(person.id),
        national_id=person.national_id,
        first_name=person.first_name,
        last_name=person.last_name,
        name=person.name,
        date_of_birth=str(person.date_of_birth) if person.date_of_birth else None,
        email=person.email,
        phone=person.phone,
        additional_info=person.additional_info,
        organizations=[],
        has_user_account=False,
        user_roles=[],
        linked_org_ids=[]
    )


@router.get("/{person_id}", response_model=PersonResponse)
def get_person(person_id: UUID, db: DB, current_user: LocalUser = CurrentUserV2, x_tenant_id: Optional[str] = None):
    """Get a specific person."""
    tenant_id = get_tenant_id(current_user, x_tenant_id)

    person = db.query(Person).filter(Person.id == person_id).first()
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")

    person_org_links = db.query(PersonOrganization).filter(
        PersonOrganization.person_id == person.id,
        PersonOrganization.tenant_id == tenant_id
    ).all()

    org_ids = [link.tenant_id for link in person_org_links]
    tenants = {t.id: t for t in db.query(Tenant).filter(Tenant.id.in_(org_ids)).all()} if org_ids else {}

    org_list = []
    linked_org_ids = set()
    for link in person_org_links:
        tenant = tenants.get(link.tenant_id)
        org_list.append({
            "tenant_id": str(link.tenant_id),
            "tenant_name": tenant.name if tenant else "Unknown",
            "role": link.role
        })
        linked_org_ids.add(str(link.tenant_id))

    asset = db.query(Asset).filter(
        Asset.person_id == person.id,
        Asset.tenant_id == tenant_id
    ).first()

    has_user = False
    user_roles = []
    if asset and asset.owner_user_id:
        user = db.query(User).filter(User.id == asset.owner_user_id).first()
        if user:
            has_user = True
            if hasattr(user, 'roles') and user.roles:
                user_roles = [{"id": str(r.id), "code": r.code, "name": r.name} for r in user.roles]

    return PersonResponse(
        id=str(person.id),
        national_id=person.national_id,
        first_name=person.first_name,
        last_name=person.last_name,
        name=person.name,
        date_of_birth=str(person.date_of_birth) if person.date_of_birth else None,
        email=person.email,
        phone=person.phone,
        additional_info=person.additional_info,
        organizations=org_list,
        has_user_account=has_user,
        user_roles=user_roles,
        linked_org_ids=list(linked_org_ids)
    )


@router.patch("/{person_id}", response_model=PersonResponse)
def update_person(person_id: UUID, db: DB, request: PersonUpdate, current_user: LocalUser = CurrentUserV2, x_tenant_id: Optional[str] = None):
    """Update a person."""
    tenant_id = get_tenant_id(current_user, x_tenant_id)

    person = db.query(Person).filter(Person.id == person_id).first()
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")

    if request.national_id is not None:
        person.national_id = request.national_id
    if request.first_name is not None:
        person.first_name = request.first_name
    if request.last_name is not None:
        person.last_name = request.last_name
    if request.date_of_birth is not None:
        person.date_of_birth = request.date_of_birth
    if request.email is not None:
        person.email = request.email
    if request.phone is not None:
        person.phone = request.phone
    if request.additional_info is not None:
        person.additional_info = request.additional_info

    db.commit()
    db.refresh(person)

    return get_person(person.id, db, current_user, x_tenant_id)


@router.delete("/{person_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_person(person_id: UUID, db: DB, current_user: LocalUser = CurrentUserV2, x_tenant_id: Optional[str] = None):
    """Delete a person."""
    tenant_id = get_tenant_id(current_user, x_tenant_id)

    person = db.query(Person).filter(Person.id == person_id).first()
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")

    db.query(PersonOrganization).filter(
        PersonOrganization.person_id == person.id,
        PersonOrganization.tenant_id == tenant_id
    ).delete()

    db.query(Asset).filter(
        Asset.person_id == person.id,
        Asset.tenant_id == tenant_id
    ).delete()

    db.delete(person)
    db.commit()


@router.post("/{person_id}/organizations", status_code=status.HTTP_201_CREATED)
def link_person_to_organization(person_id: UUID, db: DB, request: OrganizationLinkCreate, current_user: LocalUser = CurrentUserV2, x_tenant_id: Optional[str] = None):
    """Link a person to an organization (tenant)."""
    target_tenant_id = x_tenant_id or current_user.tenant_id

    person = db.query(Person).filter(Person.id == person_id).first()
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")

    existing = db.query(PersonOrganization).filter(
        PersonOrganization.person_id == person.id,
        PersonOrganization.tenant_id == target_tenant_id
    ).first()

    if existing:
        existing.role = request.role
        db.commit()
    else:
        link = PersonOrganization(
            person_id=person.id,
            tenant_id=target_tenant_id,
            role=request.role
        )
        db.add(link)
        db.commit()

    return {"status": "linked", "person_id": str(person_id), "tenant_id": str(target_tenant_id)}


@router.delete("/{person_id}/organizations/{tenant_id}", status_code=status.HTTP_204_NO_CONTENT)
def unlink_person_from_organization(person_id: UUID, tenant_id: UUID, db: DB, current_user: LocalUser = CurrentUserV2):
    """Unlink a person from an organization."""
    link = db.query(PersonOrganization).filter(
        PersonOrganization.person_id == person_id,
        PersonOrganization.tenant_id == tenant_id
    ).first()

    if not link:
        raise HTTPException(status_code=404, detail="Link not found")

    db.delete(link)
    db.commit()