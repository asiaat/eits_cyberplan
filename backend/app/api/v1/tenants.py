"""Tenants API endpoints."""
from typing import Optional, List
from uuid import uuid4
from datetime import date
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.api.deps import DB, CurrentUser
from app.core.security import get_password_hash

router = APIRouter()


class TenantUpdate(BaseModel):
    name: Optional[str] = None
    registry_code: Optional[str] = None
    legal_form: Optional[str] = None
    registration_date: Optional[date] = None
    status: Optional[str] = None
    registered_address: Optional[str] = None
    contact_address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    share_capital: Optional[float] = None
    nace_codes: Optional[List[str]] = None
    company_type: Optional[str] = None
    divisions: Optional[List[dict]] = None


class TenantResponse(BaseModel):
    id: str
    name: str
    registry_code: Optional[str] = None
    legal_form: Optional[str] = None
    registration_date: Optional[str] = None
    status: Optional[str] = None
    registered_address: Optional[str] = None
    contact_address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    share_capital: Optional[float] = None
    nace_codes: Optional[List[str]] = None
    company_type: Optional[str] = None
    divisions: List[dict] = []
    created_at: Optional[str] = None


def _get_user_tenant_id(db: DB, user) -> Optional[str]:
    """Get tenant_id from user's first membership."""
    from app.models.membership import Membership
    membership = db.query(Membership).filter(Membership.user_id == user.id).first()
    return str(membership.tenant_id) if membership and membership.tenant_id else None


def _tenant_to_response(tenant) -> dict:
    return {
        "id": str(tenant.id),
        "name": tenant.name,
        "registry_code": tenant.registry_code,
        "legal_form": tenant.legal_form,
        "registration_date": str(tenant.registration_date) if tenant.registration_date else None,
        "status": tenant.status,
        "registered_address": tenant.registered_address,
        "contact_address": tenant.contact_address,
        "phone": tenant.phone,
        "email": tenant.email,
        "website": tenant.website,
        "share_capital": float(tenant.share_capital) if tenant.share_capital else None,
        "nace_codes": tenant.nace_codes or [],
        "company_type": tenant.company_type,
        "divisions": tenant.divisions or [],
        "created_at": str(tenant.created_at) if tenant.created_at else None,
    }


class CreateOrganizationRequest(BaseModel):
    name: str
    registry_code: str
    legal_form: Optional[str] = None
    registration_date: Optional[date] = None
    registered_address: Optional[str] = None
    contact_address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    share_capital: Optional[float] = None
    nace_codes: Optional[List[str]] = None
    company_type: Optional[str] = None
    
    admin_name: str
    admin_email: str
    admin_password: str


@router.get("/", response_model=List[TenantResponse])
def list_tenants(db: DB, current_user: CurrentUser):
    """List all organizations (for super-admin)."""
    from app.models.tenant import Tenant
    tenants = db.query(Tenant).order_by(Tenant.name).all()
    return [_tenant_to_response(t) for t in tenants]


@router.get("/my-organizations")
def get_user_organizations(db: DB, current_user: CurrentUser):
    """Get organizations user has access to."""
    from app.models.tenant import Tenant
    from app.models.membership import Membership
    from app.core.permissions import get_user_permissions
    
    permissions = get_user_permissions(db, current_user)
    
    if "organizations.view" in permissions:
        # Super-admin sees all orgs
        tenants = db.query(Tenant).order_by(Tenant.name).all()
    else:
        # Regular user sees only their orgs
        memberships = db.query(Membership).filter(Membership.user_id == current_user.id).all()
        tenant_ids = [m.tenant_id for m in memberships]
        tenants = db.query(Tenant).filter(Tenant.id.in_(tenant_ids)).order_by(Tenant.name).all() if tenant_ids else []
    
    return [{"id": str(t.id), "name": t.name} for t in tenants]


@router.get("/current", response_model=TenantResponse)
def get_current_tenant(db: DB, current_user: CurrentUser):
    """Get current tenant."""
    from app.models.tenant import Tenant
    tenant_id = _get_user_tenant_id(db, current_user)
    if not tenant_id:
        return {
            "id": "default", 
            "name": "Default Organization", 
            "registry_code": None, 
            "divisions": [],
            "legal_form": None,
            "registration_date": None,
            "status": None,
            "registered_address": None,
            "contact_address": None,
            "phone": None,
            "email": None,
            "website": None,
            "share_capital": None,
            "nace_codes": [],
            "company_type": None,
            "created_at": None,
        }
    from uuid import UUID
    tenant = db.query(Tenant).filter(Tenant.id == UUID(tenant_id)).first()
    if tenant:
        return _tenant_to_response(tenant)
    return {
        "id": "default", 
        "name": "Default Organization", 
        "registry_code": None, 
        "divisions": [],
        "legal_form": None,
        "registration_date": None,
        "status": None,
        "registered_address": None,
        "contact_address": None,
        "phone": None,
        "email": None,
        "website": None,
        "share_capital": None,
        "nace_codes": [],
        "company_type": None,
        "created_at": None,
    }


@router.patch("/current", response_model=TenantResponse)
def update_current_tenant(db: DB, current_user: CurrentUser, data: TenantUpdate):
    """Update current tenant (organization)."""
    from app.models.tenant import Tenant
    tenant_id = _get_user_tenant_id(db, current_user)
    if not tenant_id:
        raise HTTPException(status_code=404, detail="No tenant found for user")
    from uuid import UUID
    tenant = db.query(Tenant).filter(Tenant.id == UUID(tenant_id)).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    if data.name is not None:
        tenant.name = data.name
    if data.registry_code is not None and data.registry_code != tenant.registry_code:
        existing = db.query(Tenant).filter(
            Tenant.registry_code == data.registry_code,
            Tenant.id != tenant.id
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="Registry code already exists")
        tenant.registry_code = data.registry_code
    if data.legal_form is not None:
        tenant.legal_form = data.legal_form
    if data.registration_date is not None:
        tenant.registration_date = data.registration_date
    if data.status is not None:
        tenant.status = data.status
    if data.registered_address is not None:
        tenant.registered_address = data.registered_address
    if data.contact_address is not None:
        tenant.contact_address = data.contact_address
    if data.phone is not None:
        tenant.phone = data.phone
    if data.email is not None:
        tenant.email = data.email
    if data.website is not None:
        tenant.website = data.website
    if data.share_capital is not None:
        tenant.share_capital = data.share_capital
    if data.nace_codes is not None:
        tenant.nace_codes = data.nace_codes
    if data.company_type is not None:
        tenant.company_type = data.company_type
    if data.divisions is not None:
        tenant.divisions = data.divisions
    
    db.commit()
    db.refresh(tenant)
    
    return _tenant_to_response(tenant)


@router.post("/", response_model=TenantResponse)
def create_organization(db: DB, current_user: CurrentUser, data: CreateOrganizationRequest):
    """Create a new organization with admin user."""
    from app.models.tenant import Tenant
    from app.models.user import User
    from app.models.membership import Membership
    from app.models.role import Role
    
    existing = db.query(Tenant).filter(Tenant.registry_code == data.registry_code).first()
    if existing:
        raise HTTPException(status_code=400, detail="Organization with this registry code already exists")
    
    existing_user = db.query(User).filter(User.email == data.admin_email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="User with this email already exists")
    
    tenant = Tenant(
        id=uuid4(),
        name=data.name,
        registry_code=data.registry_code,
        legal_form=data.legal_form,
        registration_date=data.registration_date,
        status="active",
        registered_address=data.registered_address,
        contact_address=data.contact_address,
        phone=data.phone,
        email=data.email,
        website=data.website,
        share_capital=data.share_capital,
        nace_codes=data.nace_codes,
        company_type=data.company_type,
        divisions=[],
    )
    db.add(tenant)
    db.flush()
    
    admin_role = db.query(Role).filter(Role.code == "admin").first()
    if not admin_role:
        raise HTTPException(status_code=500, detail="Admin role not found")
    
    admin_user = User(
        id=uuid4(),
        email=data.admin_email,
        name=data.admin_name,
        hashed_password=get_password_hash(data.admin_password),
        is_active=True,
    )
    db.add(admin_user)
    db.flush()
    
    membership = Membership(
        id=uuid4(),
        tenant_id=tenant.id,
        user_id=admin_user.id,
        role_id=admin_role.id,
    )
    db.add(membership)
    db.commit()
    db.refresh(tenant)
    
    return _tenant_to_response(tenant)


@router.get("/{tenant_id}", response_model=TenantResponse)
def get_tenant_by_id(tenant_id: str, db: DB, current_user: CurrentUser):
    """Get specific tenant by ID."""
    from app.models.tenant import Tenant
    from app.models.membership import Membership
    from uuid import UUID
    
    # Check if user has access to this tenant
    memberships = db.query(Membership).filter(Membership.user_id == current_user.id).all()
    user_tenant_ids = [str(m.tenant_id) for m in memberships]
    
    # Allow if user is super-admin or has membership in this org
    from app.core.permissions import get_user_permissions
    permissions = get_user_permissions(db, current_user)
    if "organizations.view" not in permissions and tenant_id not in user_tenant_ids:
        raise HTTPException(status_code=403, detail="Access denied")
    
    tenant = db.query(Tenant).filter(Tenant.id == UUID(tenant_id)).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    return _tenant_to_response(tenant)