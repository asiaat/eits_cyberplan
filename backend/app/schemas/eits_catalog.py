"""Catalog and E-ITS schemas."""
from datetime import datetime, date
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class MeasureLevel(str, Enum):
    BASE = "BASE"
    STANDARD = "STANDARD"
    HIGH = "HIGH"


class ModuleGroup(str, Enum):
    ISMS = "ISMS"
    ORP = "ORP"
    CON = "CON"
    OPS = "OPS"
    DER = "DER"
    INF = "INF"
    NET = "NET"
    SYS = "SYS"
    APP = "APP"
    IND = "IND"


class ModuleType(str, Enum):
    PROCESS = "PROCESS"
    SYSTEM = "SYSTEM"


class CatalogVersionBase(BaseModel):
    year: Optional[str] = Field(None, max_length=4)
    name: Optional[str] = Field(None, max_length=100)
    is_active: bool = False
    released_at: Optional[date] = None


class CatalogVersionCreate(CatalogVersionBase):
    pass


class CatalogVersionResponse(CatalogVersionBase):
    id: UUID
    source_name: Optional[str] = None
    source_file_hash: Optional[str] = None
    imported_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class EitsModuleBase(BaseModel):
    code: str = Field(..., max_length=50)
    name: str = Field(..., max_length=255)
    module_group: Optional[ModuleGroup] = None
    category: Optional[str] = None
    description: Optional[str] = None
    module_type: Optional[ModuleType] = None
    source_url: Optional[str] = None


class EitsModuleCreate(EitsModuleBase):
    catalog_version_id: UUID


class EitsModuleResponse(EitsModuleBase):
    id: UUID
    catalog_version_id: UUID

    model_config = ConfigDict(from_attributes=True)


class EitsModuleWithMeasures(EitsModuleResponse):
    measures: list["EitsCatalogMeasureResponse"] = []


class EitsCatalogMeasureBase(BaseModel):
    code: str = Field(..., max_length=30)
    name: str
    measure_level: MeasureLevel
    description: Optional[str] = None
    responsible_role: Optional[str] = None


class EitsCatalogMeasureCreate(EitsCatalogMeasureBase):
    module_id: UUID


class EitsCatalogMeasureResponse(EitsCatalogMeasureBase):
    id: UUID
    module_id: UUID

    model_config = ConfigDict(from_attributes=True)


class EitsThreatBase(BaseModel):
    code: str = Field(..., max_length=30)
    category: Optional[str] = None
    impact_area: Optional[str] = None
    name: str = Field(..., max_length=255)
    description: Optional[str] = None


class EitsThreatCreate(EitsThreatBase):
    version_id: UUID


class EitsThreatResponse(EitsThreatBase):
    id: UUID
    version_id: UUID

    model_config = ConfigDict(from_attributes=True)


class ModuleThreatCreate(BaseModel):
    module_id: UUID
    threat_id: UUID
    relevance_note: Optional[str] = None


class ModuleThreatResponse(BaseModel):
    id: UUID
    module_id: UUID
    threat_id: UUID
    relevance_note: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class DamageScenarioResponse(BaseModel):
    id: UUID
    code: str
    name: str
    description: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class AssetTypeCategoryResponse(BaseModel):
    id: UUID
    code: str
    name: str
    description: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class SecurityApproach(str, Enum):
    BASIC = "BASIC"
    STANDARD = "STANDARD"
    CORE = "CORE"


class SecurityProfileBase(BaseModel):
    security_approach: SecurityApproach = SecurityApproach.BASIC
    catalog_version_id: Optional[UUID] = None
    notes: Optional[str] = None


class SecurityProfileCreate(SecurityProfileBase):
    pass


class SecurityProfileUpdate(BaseModel):
    security_approach: Optional[SecurityApproach] = None
    catalog_version_id: Optional[UUID] = None
    approved_by: Optional[UUID] = None
    approved_at: Optional[datetime] = None
    notes: Optional[str] = None


class SecurityProfileResponse(SecurityProfileBase):
    id: UUID
    tenant_id: UUID
    approved_by: Optional[UUID] = None
    approved_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DamageAssessmentBase(BaseModel):
    availability_impact: int = Field(0, ge=0, le=3)
    confidentiality_impact: int = Field(0, ge=0, le=3)
    integrity_impact: int = Field(0, ge=0, le=3)
    justification: Optional[str] = None


class DamageAssessmentCreate(DamageAssessmentBase):
    business_process_id: UUID
    damage_scenario_id: UUID
    assessed_by: Optional[UUID] = None


class DamageAssessmentUpdate(BaseModel):
    availability_impact: Optional[int] = Field(None, ge=0, le=3)
    confidentiality_impact: Optional[int] = Field(None, ge=0, le=3)
    integrity_impact: Optional[int] = Field(None, ge=0, le=3)
    justification: Optional[str] = None
    assessed_by: Optional[UUID] = None


class DamageAssessmentResponse(DamageAssessmentBase):
    id: UUID
    tenant_id: UUID
    business_process_id: UUID
    damage_scenario_id: UUID
    damage_category: Optional[int] = None
    assessed_by: Optional[UUID] = None
    assessed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class ProtectionNeedLevel(str, Enum):
    NORMAL = "NORMAL"
    HIGH = "HIGH"
    VERY_HIGH = "VERY_HIGH"


class ProtectionNeedSummaryBase(BaseModel):
    protection_need: ProtectionNeedLevel = ProtectionNeedLevel.NORMAL
    confidentiality_need: ProtectionNeedLevel = ProtectionNeedLevel.NORMAL
    integrity_need: ProtectionNeedLevel = ProtectionNeedLevel.NORMAL
    availability_need: ProtectionNeedLevel = ProtectionNeedLevel.NORMAL
    justification: Optional[str] = None


class ProtectionNeedSummaryCreate(ProtectionNeedSummaryBase):
    business_process_id: UUID


class ProtectionNeedSummaryUpdate(BaseModel):
    protection_need: Optional[ProtectionNeedLevel] = None
    confidentiality_need: Optional[ProtectionNeedLevel] = None
    integrity_need: Optional[ProtectionNeedLevel] = None
    availability_need: Optional[ProtectionNeedLevel] = None
    justification: Optional[str] = None
    approved_by: Optional[UUID] = None
    approved_at: Optional[datetime] = None


class ProtectionNeedSummaryResponse(ProtectionNeedSummaryBase):
    id: UUID
    tenant_id: UUID
    business_process_id: UUID
    approved_by: Optional[UUID] = None
    approved_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AssetModuleMappingBase(BaseModel):
    asset_id: UUID
    module_id: UUID
    justification: Optional[str] = None


class AssetModuleMappingCreate(AssetModuleMappingBase):
    pass


class AssetModuleMappingUpdate(BaseModel):
    justification: Optional[str] = None


class ModuleInfo(BaseModel):
    id: UUID
    code: str
    name: str
    module_group: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class AssetModuleMappingResponse(AssetModuleMappingBase):
    id: UUID
    tenant_id: UUID
    modeled_by: Optional[UUID] = None
    modeled_at: Optional[datetime] = None
    module: Optional[ModuleInfo] = None

    model_config = ConfigDict(from_attributes=True)


class PearoStatus(str, Enum):
    P = "P"
    E = "E"
    A = "A"
    R = "R"
    O = "O"


class ImrPriority(str, Enum):
    P1 = "P1"
    P2 = "P2"
    P3 = "P3"


class ImrItemBase(BaseModel):
    measure_id: UUID
    pearo_status: PearoStatus = PearoStatus.E
    implementation_description: Optional[str] = None
    non_implementation_justification: Optional[str] = None
    partial_scope_description: Optional[str] = None
    due_date: Optional[date] = None
    next_review_date: Optional[date] = None
    priority: ImrPriority = ImrPriority.P2
    verification_method: Optional[str] = None


class ImrItemCreate(ImrItemBase):
    asset_module_mapping_id: Optional[UUID] = None
    is_process_module_measure: bool = False
    responsible_user_id: Optional[UUID] = None


class ImrItemUpdate(BaseModel):
    pearo_status: Optional[PearoStatus] = None
    implementation_description: Optional[str] = None
    non_implementation_justification: Optional[str] = None
    partial_scope_description: Optional[str] = None
    responsible_user_id: Optional[UUID] = None
    due_date: Optional[date] = None
    next_review_date: Optional[date] = None
    priority: Optional[ImrPriority] = None
    risk_acceptance_approved_by: Optional[UUID] = None
    risk_acceptance_date: Optional[datetime] = None
    verification_method: Optional[str] = None
    last_verified_at: Optional[datetime] = None


class MeasureInfo(BaseModel):
    id: UUID
    code: str
    name: str
    measure_level: str

    model_config = ConfigDict(from_attributes=True)


class ImrItemResponse(ImrItemBase):
    id: UUID
    tenant_id: UUID
    asset_module_mapping_id: Optional[UUID] = None
    is_process_module_measure: bool = False
    responsible_user_id: Optional[UUID] = None
    risk_acceptance_approved_by: Optional[UUID] = None
    risk_acceptance_date: Optional[datetime] = None
    last_verified_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    measure: Optional[MeasureInfo] = None

    model_config = ConfigDict(from_attributes=True)


class ImrSummaryResponse(BaseModel):
    tenant_id: UUID
    pearo_status: str
    measure_level: str
    measure_count: int
    overdue_count: int


class AssetProtectionOverview(BaseModel):
    tenant_id: UUID
    asset_id: UUID
    asset_index: Optional[str] = None
    asset_name: str
    asset_category: Optional[str] = None
    protection_need: str
    mapped_module_count: int
    imr_item_count: int
    implemented_count: int
    not_implemented_count: int


class RiskMatrixCell(BaseModel):
    tenant_id: UUID
    impact_score: Optional[int] = None
    likelihood_score: Optional[int] = None
    risk_count: int
    risk_titles: list[str]


class DamageCategoryThresholdBase(BaseModel):
    damage_scenario_id: UUID
    negligible_description: Optional[str] = None
    limited_description: Optional[str] = None
    serious_description: Optional[str] = None
    catastrophic_description: Optional[str] = None


class DamageCategoryThresholdCreate(DamageCategoryThresholdBase):
    pass


class DamageCategoryThresholdUpdate(BaseModel):
    negligible_description: Optional[str] = None
    limited_description: Optional[str] = None
    serious_description: Optional[str] = None
    catastrophic_description: Optional[str] = None
    approved_by: Optional[UUID] = None


class DamageCategoryThresholdResponse(DamageCategoryThresholdBase):
    id: UUID
    tenant_id: UUID
    approved_by: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProcessModuleAssignmentBase(BaseModel):
    module_id: UUID
    is_applicable: bool = True
    non_applicability_justification: Optional[str] = None


class ProcessModuleAssignmentCreate(ProcessModuleAssignmentBase):
    pass


class ProcessModuleAssignmentUpdate(BaseModel):
    is_applicable: Optional[bool] = None
    non_applicability_justification: Optional[str] = None


class ProcessModuleAssignmentResponse(ProcessModuleAssignmentBase):
    id: UUID
    tenant_id: UUID
    assigned_by: Optional[UUID] = None
    assigned_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RiskMeasureLinkBase(BaseModel):
    risk_id: UUID
    measure_id: Optional[UUID] = None
    imr_item_id: Optional[UUID] = None
    custom_measure_name: Optional[str] = None
    custom_measure_description: Optional[str] = None


class RiskMeasureLinkCreate(RiskMeasureLinkBase):
    pass


class RiskMeasureLinkResponse(RiskMeasureLinkBase):
    id: UUID
    tenant_id: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RiskV2Base(BaseModel):
    title: str = Field(..., max_length=255)
    scenario: Optional[str] = None
    threat_id: Optional[UUID] = None
    asset_id: Optional[UUID] = None
    business_process_id: Optional[UUID] = None
    likelihood_score: Optional[int] = Field(None, ge=0, le=3)
    impact_score: Optional[int] = Field(None, ge=0, le=3)
    risk_rating: Optional[str] = None
    treatment_type: Optional[str] = None
    residual_risk_level: Optional[str] = None
    owner_user_id: Optional[UUID] = None


class RiskV2Create(RiskV2Base):
    pass


class RiskV2Update(BaseModel):
    title: Optional[str] = None
    scenario: Optional[str] = None
    threat_id: Optional[UUID] = None
    asset_id: Optional[UUID] = None
    business_process_id: Optional[UUID] = None
    likelihood_score: Optional[int] = Field(None, ge=0, le=3)
    impact_score: Optional[int] = Field(None, ge=0, le=3)
    risk_rating: Optional[str] = None
    treatment_type: Optional[str] = None
    residual_risk_level: Optional[str] = None
    status: Optional[str] = None
    owner_user_id: Optional[UUID] = None


class RiskV2Response(RiskV2Base):
    id: UUID
    tenant_id: UUID
    risk_score: Optional[int] = None
    status: Optional[str] = None
    accepted_by: Optional[UUID] = None
    accepted_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


from app.schemas.asset import AssetListItem
from app.schemas.business_process import BusinessProcessListItem