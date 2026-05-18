"""Export all models for convenience."""
from app.models.app_tenant import AppTenant, GlobalUser, TenantUser
from app.models.local_user import LocalUser, EITSRole, UserRole
from app.models.tenant import Tenant
from app.models.user import User
from app.models.role import Role
from app.models.permission import Permission
from app.models.role_permission import RolePermission
from app.models.e_its_role_permission import EITSRolePermission
from app.models.membership import Membership
from app.models.business_process import BusinessProcess
from app.models.asset import Asset
from app.models.asset_relation import AssetRelation
from app.models.process_asset import ProcessAsset
from app.models.eits_catalog_version import EitsCatalogVersion
from app.models.eits_module import EitsModule
from app.models.eits_measure import EitsMeasure
from app.models.eits_module_measure import EitsModuleMeasure
from app.models.object_module_mapping import ObjectModuleMapping
from app.models.implementation_plan_item import ImplementationPlanItem
from app.models.risk import Risk
from app.models.evidence import Evidence
from app.models.evidence_link import EvidenceLink
from app.models.audit_log import AuditLog
from app.models.comment import Comment
from app.models.organization_people import OrganizationPeople
from app.models.person import Person, PersonOrganization
from app.models.alert import Alert
from app.models.eits_catalog_measure import EitsCatalogMeasure
from app.models.eits_threat import EitsThreat, ModuleThreat
from app.models.damage_scenario import DamageScenario
from app.models.asset_type_category import AssetTypeCategory
from app.models.security_profile import SecurityProfile
from app.models.damage_assessment import DamageAssessment
from app.models.protection_need_summary import ProtectionNeedSummary
from app.models.asset_module_mapping import AssetModuleMapping
from app.models.imr_item import ImrItem
from app.models.risk_measure_link import RiskMeasureLink, DamageCategoryThreshold, ProcessModuleAssignment

__all__ = [
    # Tier A - Subscription Layer
    "AppTenant",
    "GlobalUser",
    "TenantUser",
    # Tier B - Per-Tenant
    "LocalUser",
    "EITSRole",
    "UserRole",
    # Legacy (to be migrated)
    "Tenant",
    "User",
    "Role",
    "Permission",
    "RolePermission",
    "EITSRolePermission",
    "Membership",
    "BusinessProcess",
    "Asset",
    "AssetRelation",
    "ProcessAsset",
    "EitsCatalogVersion",
    "EitsModule",
    "EitsMeasure",
    "EitsModuleMeasure",
    "ObjectModuleMapping",
    "ImplementationPlanItem",
    "Risk",
    "Evidence",
    "EvidenceLink",
    "AuditLog",
    "Comment",
    "OrganizationPeople",
    "Person",
    "PersonOrganization",
    "Alert",
    # E-ITS v2 - Tier A
    "EitsCatalogMeasure",
    "EitsThreat",
    "ModuleThreat",
    "DamageScenario",
    # E-ITS v2 - Tier B
    "AssetTypeCategory",
    "SecurityProfile",
    "DamageAssessment",
    "ProtectionNeedSummary",
    "AssetModuleMapping",
    "ImrItem",
    "RiskMeasureLink",
    "DamageCategoryThreshold",
    "ProcessModuleAssignment",
]