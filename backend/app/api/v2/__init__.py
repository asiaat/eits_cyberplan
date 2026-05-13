"""API v2 - New IAM system with Tier A/B multi-tenancy."""
from fastapi import APIRouter

from app.api.v2 import auth, tenants, users, organizations, alerts, roles

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["v2-auth"])
api_router.include_router(tenants.router, prefix="/tenants", tags=["v2-tenants"])
api_router.include_router(users.router, prefix="/users", tags=["v2-users"])
api_router.include_router(organizations.router, prefix="/organizations", tags=["v2-organizations"])
api_router.include_router(alerts.router, prefix="/alerts", tags=["v2-alerts"])
api_router.include_router(roles.router, prefix="/roles", tags=["v2-roles"])