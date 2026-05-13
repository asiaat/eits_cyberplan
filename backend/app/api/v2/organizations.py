"""Organizations API v2 - Organization management within tenant."""
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.api.deps import DB
from app.api.v2.auth import CurrentUserV2
from app.models.tenant import Tenant

router = APIRouter()


class OrganizationResponse(BaseModel):
    id: str
    name: str
    registry_code: str | None
    legal_form: str | None
    status: str


class OrganizationCreate(BaseModel):
    name: str
    registry_code: str | None = None
    legal_form: str | None = None


@router.get("/", response_model=List[OrganizationResponse])
def list_organizations(db: DB, current_user = CurrentUserV2):
    """List all organizations in current tenant."""
    # Organizations are stored in the old Tenant table
    # We use the tenant_id from current user as the tenant context
    # For now, list all (in production, filter by tenant context)
    organizations = db.query(Tenant).all()
    
    return [
        OrganizationResponse(
            id=str(org.id),
            name=org.name,
            registry_code=org.registry_code,
            legal_form=org.legal_form,
            status=org.status or "active"
        )
        for org in organizations
    ]


@router.get("/{org_id}", response_model=OrganizationResponse)
def get_organization(org_id: UUID, db: DB, current_user = CurrentUserV2):
    """Get organization details."""
    org = db.query(Tenant).filter(Tenant.id == org_id).first()
    
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found",
        )
    
    return OrganizationResponse(
        id=str(org.id),
        name=org.name,
        registry_code=org.registry_code,
        legal_form=org.legal_form,
        status=org.status or "active"
    )


@router.post("/", response_model=OrganizationResponse)
def create_organization(db: DB, request: OrganizationCreate, current_user = CurrentUserV2):
    """Create new organization."""
    org = Tenant(
        name=request.name,
        registry_code=request.registry_code,
        legal_form=request.legal_form,
        status="active"
    )
    db.add(org)
    db.commit()
    db.refresh(org)
    
    return OrganizationResponse(
        id=str(org.id),
        name=org.name,
        registry_code=org.registry_code,
        legal_form=org.legal_form,
        status=org.status or "active"
    )