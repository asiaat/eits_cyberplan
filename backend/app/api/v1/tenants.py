"""Tenants API endpoints."""
from fastapi import APIRouter, Depends

from app.api.deps import DB, CurrentUser

router = APIRouter()


@router.get("/current")
def get_current_tenant(db: DB, current_user: CurrentUser):
    """Get current tenant."""
    from app.models.tenant import Tenant
    tenant = db.query(Tenant).filter(Tenant.id == current_user.tenant_id).first()
    if tenant:
        return {"id": tenant.id, "name": tenant.name}
    return {"id": "default", "name": "Default Organization"}