"""Tenants API v2 - Subscription management."""
import json
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.api.deps import DB
from app.api.v2.auth import CurrentUserV2
from app.models.app_tenant import AppTenant, TenantUser, GlobalUser
from app.models.local_user import LocalUser
from app.core.security import get_password_hash

router = APIRouter()


class TenantResponse(BaseModel):
    id: str
    name: str
    status: str
    plan: str | None
    created_at: str
    registry_code: Optional[str] = None
    legal_form: Optional[str] = None
    registered_address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    divisions: Optional[List[dict]] = []


class TenantCreate(BaseModel):
    name: str
    plan: str = "standard"
    registry_code: Optional[str] = None
    legal_form: Optional[str] = None
    registered_address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    admin_name: Optional[str] = None
    admin_email: Optional[str] = None
    admin_password: Optional[str] = None


class TenantUpdate(BaseModel):
    name: Optional[str] = None
    registry_code: Optional[str] = None
    legal_form: Optional[str] = None
    registered_address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    divisions: Optional[list] = None


@router.get("/", response_model=List[TenantResponse])
def list_tenants(db: DB, current_user = CurrentUserV2):
    """List all tenants the current user has access to."""
    tenant_users = db.query(TenantUser).filter(
        TenantUser.user_id == current_user.global_user_id
    ).all()
    
    tenant_ids = [tu.tenant_id for tu in tenant_users]
    tenants = db.query(AppTenant).filter(AppTenant.id.in_(tenant_ids)).all()
    
    return [
        TenantResponse(
            id=str(t.id),
            name=t.name,
            status=t.status,
            plan=t.plan,
            created_at=str(t.created_at)
        )
        for t in tenants
    ]


@router.get("/my-organizations", response_model=List[TenantResponse])
def get_my_organizations(db: DB, current_user = CurrentUserV2):
    """Get user's organizations (tenants)."""
    user_id = current_user.global_user_id
    
    tenant_users = db.query(TenantUser).filter(
        TenantUser.user_id == user_id
    ).all()
    
    if not tenant_users:
        return []
    
    tenant_ids = [tu.tenant_id for tu in tenant_users]
    tenants = db.query(AppTenant).filter(AppTenant.id.in_(tenant_ids)).all()
    
    return [
        TenantResponse(
            id=str(t.id),
            name=t.name,
            status=t.status,
            plan=t.plan,
            created_at=str(t.created_at),
            registry_code=t.registry_code,
            legal_form=t.legal_form,
            registered_address=t.registered_address,
            phone=t.phone,
            email=t.email,
            divisions=json.loads(t.divisions) if t.divisions else []
        )
        for t in tenants
    ]


@router.get("/{tenant_id}", response_model=TenantResponse)
def get_tenant(tenant_id: UUID, db: DB, current_user = CurrentUserV2):
    """Get tenant details."""
    # Verify access
    tenant_user = db.query(TenantUser).filter(
        TenantUser.user_id == current_user.global_user_id,
        TenantUser.tenant_id == tenant_id
    ).first()
    
    if not tenant_user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No access to this tenant",
        )
    
    tenant = db.query(AppTenant).filter(AppTenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found",
        )
    
    divisions = []
    if tenant.divisions:
        try:
            divisions = json.loads(tenant.divisions)
        except (json.JSONDecodeError, TypeError):
            divisions = []
    
    return TenantResponse(
        id=str(tenant.id),
        name=tenant.name,
        status=tenant.status,
        plan=tenant.plan,
        created_at=str(tenant.created_at),
        registry_code=tenant.registry_code,
        legal_form=tenant.legal_form,
        registered_address=tenant.registered_address,
        phone=tenant.phone,
        email=tenant.email,
        divisions=divisions
    )


@router.patch("/{tenant_id}", response_model=TenantResponse)
def update_tenant(tenant_id: UUID, db: DB, request: TenantUpdate, current_user = CurrentUserV2):
    """Update tenant details."""
    tenant_user = db.query(TenantUser).filter(
        TenantUser.user_id == current_user.global_user_id,
        TenantUser.tenant_id == tenant_id
    ).first()
    
    if not tenant_user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No access to this tenant",
        )
    
    tenant = db.query(AppTenant).filter(AppTenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found",
        )
    
    if request.name is not None:
        tenant.name = request.name
    if request.registry_code is not None:
        tenant.registry_code = request.registry_code
    if request.legal_form is not None:
        tenant.legal_form = request.legal_form
    if request.registered_address is not None:
        tenant.registered_address = request.registered_address
    if request.phone is not None:
        tenant.phone = request.phone
    if request.email is not None:
        tenant.email = request.email
    if request.divisions is not None:
        print(f"DEBUG: Saving divisions: {request.divisions}")
        tenant.divisions = json.dumps(request.divisions)
        print(f"DEBUG: Tenant divisions set to: {tenant.divisions}")
    
    db.commit()
    db.refresh(tenant)
    print(f"DEBUG: After commit, tenant.divisions = {tenant.divisions}")
    
    divisions = []
    if tenant.divisions:
        try:
            divisions = json.loads(tenant.divisions)
        except (json.JSONDecodeError, TypeError):
            divisions = []
    
    return TenantResponse(
        id=str(tenant.id),
        name=tenant.name,
        status=tenant.status,
        plan=tenant.plan,
        created_at=str(tenant.created_at),
        registry_code=tenant.registry_code,
        legal_form=tenant.legal_form,
        registered_address=tenant.registered_address,
        phone=tenant.phone,
        email=tenant.email,
        divisions=divisions
    )


@router.post("/", response_model=TenantResponse)
def create_tenant(db: DB, request: TenantCreate, current_user = CurrentUserV2):
    """Create new tenant with organization details and optional admin user."""
    tenant = AppTenant(
        name=request.name,
        status="active",
        plan=request.plan,
        registry_code=request.registry_code,
        legal_form=request.legal_form,
        registered_address=request.registered_address,
        phone=request.phone,
        email=request.email
    )
    db.add(tenant)
    db.commit()
    db.refresh(tenant)

    # Add current user to new tenant
    tenant_user = TenantUser(
        tenant_id=tenant.id,
        user_id=current_user.global_user_id
    )
    db.add(tenant_user)
    db.commit()

    # Create admin user if provided
    if request.admin_email and request.admin_password and request.admin_name:
        # Check if global user exists
        global_user = db.query(GlobalUser).filter(GlobalUser.email == request.admin_email).first()
        
        if not global_user:
            global_user = GlobalUser(
                email=request.admin_email,
                password_hash=get_password_hash(request.admin_password)
            )
            db.add(global_user)
            db.commit()
            db.refresh(global_user)

        # Create local user for this tenant
        local_user = LocalUser(
            global_user_id=global_user.id,
            tenant_id=tenant.id,
            full_name=request.admin_name,
            is_active=True
        )
        db.add(local_user)
        db.commit()

    return TenantResponse(
        id=str(tenant.id),
        name=tenant.name,
        status=tenant.status,
        plan=tenant.plan,
        created_at=str(tenant.created_at),
        registry_code=tenant.registry_code,
        legal_form=tenant.legal_form,
        registered_address=tenant.registered_address,
        phone=tenant.phone,
        email=tenant.email
    )