"""Persons API endpoints - Tenant-scoped People Directory."""
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, selectinload

from app.api.deps import DB, CurrentUser
from app.models.user import User
from app.models.membership import Membership
from app.models.person import Person, PersonOrganization
from app.models.tenant import Tenant
from app.models.asset import Asset
from app.models.role import Role
from app.core.permissions import has_permission

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

    model_config = {"from_attributes": True}


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


@router.get("/", response_model=List[PersonResponse])
def list_persons(db: DB, current_user: CurrentUser, search: Optional[str] = None):
    """List all persons in the current user's tenant (cluster)."""
    user_membership = db.query(Membership).filter(Membership.user_id == current_user.id).first()
    if not user_membership:
        return []
    tenant_id = user_membership.tenant_id

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
    person_ids = [p.id for p in persons]

    person_org_links = db.query(PersonOrganization).filter(
        PersonOrganization.person_id.in_(person_ids)
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
        Asset.owner_user_id.isnot(None)
    ).all() if person_ids else []

    owner_user_ids = {a.owner_user_id for a in assets if a.owner_user_id}
    user_memberships = db.query(Membership).options(
        selectinload(Membership.role)
    ).filter(Membership.user_id.in_(owner_user_ids)).all() if owner_user_ids else []

    memberships_by_user = {}
    for m in user_memberships:
        memberships_by_user.setdefault(m.user_id, []).append(m)

    assets_by_owner = {a.owner_user_id: a for a in assets}

    result = []
    for person in persons:
        person_links = links_by_person.get(person.id, [])
        orgs = []
        for link in person_links:
            tenant = tenants.get(link.tenant_id)
            if tenant:
                orgs.append({
                    "tenant_id": str(link.tenant_id),
                    "tenant_name": tenant.name,
                    "role": link.role
                })

        asset = assets_by_owner.get(person.id)
        has_user = asset is not None
        user_roles = []
        if has_user:
            for m in memberships_by_user.get(person.id, []):
                if m.role:
                    user_roles.append({
                        "id": m.role.id,
                        "code": m.role.code,
                        "name": m.role.name,
                        "is_default": m.role.is_default,
                    })

        result.append(PersonResponse(
            id=str(person.id),
            national_id=person.national_id,
            first_name=person.first_name,
            last_name=person.last_name,
            name=person.name,
            date_of_birth=str(person.date_of_birth) if person.date_of_birth else None,
            email=person.email,
            phone=person.phone,
            additional_info=person.additional_info,
            organizations=orgs,
            has_user_account=has_user,
            user_roles=user_roles,
            linked_org_ids=list(linked_org_ids_by_person.get(person.id, set())),
        ))

    return result


@router.post("/", response_model=PersonResponse)
def create_person(db: DB, current_user: CurrentUser, data: PersonCreate):
    """Create a new person in the current user's tenant."""
    if not has_permission(db, current_user, "people.create"):
        raise HTTPException(status_code=403, detail="Permission denied")

    user_membership = db.query(Membership).filter(Membership.user_id == current_user.id).first()
    if not user_membership:
        raise HTTPException(status_code=403, detail="No tenant membership")

    from uuid import uuid4

    person = Person(
        id=uuid4(),
        national_id=data.national_id,
        first_name=data.first_name,
        last_name=data.last_name,
        date_of_birth=data.date_of_birth,
        email=data.email,
        phone=data.phone,
        additional_info=data.additional_info,
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
        linked_org_ids=[],
    )


@router.get("/{person_id}", response_model=PersonResponse)
def get_person(db: DB, current_user: CurrentUser, person_id: str):
    """Get a specific person."""
    user_membership = db.query(Membership).filter(Membership.user_id == current_user.id).first()
    if not user_membership:
        raise HTTPException(status_code=403, detail="No tenant membership")
    tenant_id = user_membership.tenant_id

    person = db.query(Person).filter(Person.id == UUID(person_id)).first()
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")

    person_links = db.query(PersonOrganization).filter(
        PersonOrganization.person_id == person.id
    ).all()

    orgs = []
    for link in person_links:
        tenant = db.query(Tenant).filter(Tenant.id == link.tenant_id).first()
        if tenant:
            orgs.append({
                "tenant_id": str(link.tenant_id),
                "tenant_name": tenant.name,
                "role": link.role
            })

    asset = db.query(Asset).filter(Asset.person_id == person.id).first()
    has_user = asset is not None and asset.owner_user_id is not None
    user_roles = []

    if has_user:
        memberships = db.query(Membership).options(
            selectinload(Membership.role)
        ).filter(Membership.user_id == asset.owner_user_id).all()
        for m in memberships:
            if m.role:
                user_roles.append({
                    "id": m.role.id,
                    "code": m.role.code,
                    "name": m.role.name,
                    "is_default": m.role.is_default,
                })

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
        organizations=orgs,
        has_user_account=has_user,
        user_roles=user_roles,
        linked_org_ids=[str(link.tenant_id) for link in person_links],
    )


@router.patch("/{person_id}", response_model=PersonResponse)
def update_person(db: DB, current_user: CurrentUser, person_id: str, data: PersonUpdate):
    """Update a person."""
    if not has_permission(db, current_user, "people.edit"):
        raise HTTPException(status_code=403, detail="Permission denied")

    person = db.query(Person).filter(Person.id == UUID(person_id)).first()
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")

    if data.national_id is not None:
        person.national_id = data.national_id
    if data.first_name is not None:
        person.first_name = data.first_name
    if data.last_name is not None:
        person.last_name = data.last_name
    if data.date_of_birth is not None:
        person.date_of_birth = data.date_of_birth
    if data.email is not None:
        person.email = data.email
    if data.phone is not None:
        person.phone = data.phone
    if data.additional_info is not None:
        person.additional_info = data.additional_info

    db.commit()
    db.refresh(person)

    person_links = db.query(PersonOrganization).filter(
        PersonOrganization.person_id == person.id
    ).all()
    orgs = []
    for link in person_links:
        tenant = db.query(Tenant).filter(Tenant.id == link.tenant_id).first()
        if tenant:
            orgs.append({
                "tenant_id": str(link.tenant_id),
                "tenant_name": tenant.name,
                "role": link.role
            })

    asset = db.query(Asset).filter(Asset.person_id == person.id).first()
    has_user = asset is not None and asset.owner_user_id is not None
    user_roles = []

    if has_user:
        memberships = db.query(Membership).options(
            selectinload(Membership.role)
        ).filter(Membership.user_id == asset.owner_user_id).all()
        for m in memberships:
            if m.role:
                user_roles.append({
                    "id": m.role.id,
                    "code": m.role.code,
                    "name": m.role.name,
                    "is_default": m.role.is_default,
                })

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
        organizations=orgs,
        has_user_account=has_user,
        user_roles=user_roles,
        linked_org_ids=[str(link.tenant_id) for link in person_links],
    )


@router.delete("/{person_id}")
def delete_person(db: DB, current_user: CurrentUser, person_id: str):
    """Delete a person. Fails if person has any worker assets (referential integrity)."""
    if not has_permission(db, current_user, "people.delete"):
        raise HTTPException(status_code=403, detail="Permission denied")

    person = db.query(Person).filter(Person.id == UUID(person_id)).first()
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")

    worker_assets = db.query(Asset).filter(
        Asset.person_id == person.id,
        Asset.asset_type == "worker"
    ).count()
    if worker_assets > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete person: {worker_assets} worker(s) still linked. Unlink them first."
        )

    db.query(PersonOrganization).filter(PersonOrganization.person_id == person.id).delete()
    db.query(Asset).filter(Asset.person_id == person.id).delete()
    db.delete(person)
    db.commit()

    return {"message": "Person deleted"}


@router.post("/{person_id}/organizations", response_model=dict)
def link_person_to_organization(db: DB, current_user: CurrentUser, person_id: str, data: OrganizationLinkCreate):
    """Link a person to the current user's organization. Creates both PersonOrganization and Asset (worker)."""
    if not has_permission(db, current_user, "people.edit"):
        raise HTTPException(status_code=403, detail="Permission denied")

    user_membership = db.query(Membership).filter(Membership.user_id == current_user.id).first()
    if not user_membership:
        raise HTTPException(status_code=403, detail="No tenant membership")
    tenant_id = user_membership.tenant_id

    person = db.query(Person).filter(Person.id == UUID(person_id)).first()
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")

    existing_asset = db.query(Asset).filter(
        Asset.person_id == person.id,
        Asset.tenant_id == tenant_id,
        Asset.asset_type == "worker"
    ).first()
    if existing_asset:
        if data.role is not None:
            existing_asset.name = person.name
            existing_asset.description = person.email
        if data.role is not None:
            person_org = db.query(PersonOrganization).filter(
                PersonOrganization.person_id == person.id,
                PersonOrganization.tenant_id == tenant_id
            ).first()
            if person_org:
                person_org.role = data.role
            else:
                from uuid import uuid4
                po = PersonOrganization(id=uuid4(), person_id=person.id, tenant_id=tenant_id, role=data.role)
                db.add(po)
        db.commit()
        return {"message": "Person already linked, updated", "tenant_id": str(tenant_id), "role": data.role}

    from uuid import uuid4

    if data.role is not None:
        person_org = db.query(PersonOrganization).filter(
            PersonOrganization.person_id == person.id,
            PersonOrganization.tenant_id == tenant_id
        ).first()
        if person_org:
            person_org.role = data.role
        else:
            po = PersonOrganization(id=uuid4(), person_id=person.id, tenant_id=tenant_id, role=data.role)
            db.add(po)
    else:
        existing_po = db.query(PersonOrganization).filter(
            PersonOrganization.person_id == person.id,
            PersonOrganization.tenant_id == tenant_id
        ).first()
        if not existing_po:
            po = PersonOrganization(id=uuid4(), person_id=person.id, tenant_id=tenant_id, role=None)
            db.add(po)

    asset = Asset(
        id=uuid4(),
        tenant_id=tenant_id,
        name=person.name,
        asset_type="worker",
        description=person.email,
        person_id=person.id,
    )
    db.add(asset)
    db.commit()

    return {"message": "Person linked to organization", "tenant_id": str(tenant_id), "role": data.role}


@router.delete("/{person_id}/organizations/{tenant_id}")
def unlink_person_from_organization(db: DB, current_user: CurrentUser, person_id: str, tenant_id: str):
    """Unlink a person from an organization. Removes both PersonOrganization and the worker Asset."""
    if not has_permission(db, current_user, "people.edit"):
        raise HTTPException(status_code=403, detail="Permission denied")

    link = db.query(PersonOrganization).filter(
        PersonOrganization.person_id == UUID(person_id),
        PersonOrganization.tenant_id == UUID(tenant_id)
    ).first()

    if not link:
        raise HTTPException(status_code=404, detail="Link not found")

    db.query(Asset).filter(
        Asset.person_id == UUID(person_id),
        Asset.tenant_id == UUID(tenant_id),
        Asset.asset_type == "worker"
    ).delete()

    db.delete(link)
    db.commit()

    return {"message": "Person unlinked from organization"}
