from fastapi import APIRouter

from app.api.v1 import auth, users, tenants, catalog, business_processes, assets, mappings, implementation_plan, risks, evidences, dashboard, reports, roles, organization, alerts

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(tenants.router, prefix="/tenants", tags=["tenants"])
api_router.include_router(catalog.router, prefix="/catalog", tags=["catalog"])
api_router.include_router(business_processes.router, prefix="/business-processes", tags=["business-processes"])
api_router.include_router(assets.router, prefix="/assets", tags=["assets"])
api_router.include_router(mappings.router, prefix="/mappings", tags=["mappings"])
api_router.include_router(implementation_plan.router, prefix="/implementation-plan", tags=["implementation-plan"])
api_router.include_router(risks.router, prefix="/risks", tags=["risks"])
api_router.include_router(evidences.router, prefix="/evidences", tags=["evidences"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
api_router.include_router(reports.router, prefix="/reports", tags=["reports"])
api_router.include_router(roles.router, prefix="/roles", tags=["roles"])
api_router.include_router(organization.router, prefix="/organization", tags=["organization"])
api_router.include_router(alerts.router, prefix="/alerts", tags=["alerts"])