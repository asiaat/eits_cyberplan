"""Tenants API v2 - Subscription management."""
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.api.deps import DB
from app.api.v2.auth import CurrentUserV2
from app.models.app_tenant import AppTenant, TenantUser

router = APIRouter()


class TenantResponse(BaseModel):
    id: str
    name: str
    status: str
    plan: str | None
    created_at: str


class TenantCreate(BaseModel):
    name: str
    plan: str = "standard"


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
    
    return TenantResponse(
        id=str(tenant.id),
        name=tenant.name,
        status=tenant.status,
        plan=tenant.plan,
        created_at=str(tenant.created_at)
    )


@router.post("/", response_model=TenantResponse)
def create_tenant(db: DB, request: TenantCreate, current_user = CurrentUserV2):
    """Create new tenant (admin only)."""
    # In production, check if user has admin role
    tenant = AppTenant(
        name=request.name,
        status="active",
        plan=request.plan
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
    
    return TenantResponse(
        id=str(tenant.id),
        name=tenant.name,
        status=tenant.status,
        plan=tenant.plan,
        created_at=str(tenant.created_at)
    )