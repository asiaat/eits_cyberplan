"""API v2 - New IAM system with Tier A/B multi-tenancy."""
from fastapi import APIRouter

from app.api.v2 import auth, tenants, users, organizations, alerts, roles, persons, organization
from app.api.v2 import business_processes, assets, targets
from app.api.v2 import catalog, security_profiles, damage_assessments, asset_module_mappings, imr_items, risks_v2
from app.api.v2 import bp_evidences, evidence_upload, turbeviis

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["v2-auth"])
api_router.include_router(tenants.router, prefix="/tenants", tags=["v2-tenants"])
api_router.include_router(users.router, prefix="/users", tags=["v2-users"])
api_router.include_router(organizations.router, prefix="/organizations", tags=["v2-organizations"])
api_router.include_router(persons.router, prefix="/persons", tags=["v2-persons"])
api_router.include_router(organization.router, prefix="/organization", tags=["v2-organization"])
api_router.include_router(alerts.router, prefix="/alerts", tags=["v2-alerts"])
api_router.include_router(roles.router, prefix="/roles", tags=["v2-roles"])
api_router.include_router(business_processes.router, prefix="/business-processes", tags=["v2-business-processes"])
api_router.include_router(assets.router, prefix="/assets", tags=["v2-assets"])
api_router.include_router(targets.router, prefix="/targets", tags=["v2-targets"])
api_router.include_router(catalog.router, prefix="/catalog", tags=["v2-catalog"])
api_router.include_router(security_profiles.router, prefix="/security-profiles", tags=["v2-security-profiles"])
api_router.include_router(damage_assessments.router, prefix="/eits", tags=["v2-eits"])
api_router.include_router(asset_module_mappings.router, prefix="/asset-module-mappings", tags=["v2-asset-mappings"])
api_router.include_router(imr_items.router, prefix="/imr", tags=["v2-imr"])
api_router.include_router(risks_v2.router, prefix="/risks", tags=["v2-risks"])
api_router.include_router(bp_evidences.router, tags=["v2-bp-evidences"])
api_router.include_router(evidence_upload.router, tags=["v2-evidence"])
api_router.include_router(turbeviis.router, prefix="/turbeviis", tags=["v2-turbeviis"])