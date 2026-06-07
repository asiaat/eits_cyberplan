"""Asset schemas."""
from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class AssetType(str, Enum):
    INFORMATION_ASSET = "information_asset"
    SOFTWARE = "software"
    HARDWARE = "hardware"
    SERVICE = "service"
    DATA = "data"
    COMPETENCE = "competence"
    OTHER = "other"


class Criticality(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class LifecycleStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    DEPRECATED = "deprecated"
    RETIRED = "retired"


class TargetObjectType(str, Enum):
    """E-ITS Target Object categories - used when is_grouped=True"""
    APP = "APP"
    SYS = "SYS"
    NET = "NET"
    INF = "INF"
    IND = "IND"


class ProtectionNeedLevel(str, Enum):
    NORMAL = "normal"
    HIGH = "high"
    VERY_HIGH = "very_high"
    UNKNOWN = "unknown"


class OwnerInfo(BaseModel):
    """Minimal user info for owner display."""
    id: UUID
    name: str
    email: str

    model_config = ConfigDict(from_attributes=True)


class LinkedProcessInfo(BaseModel):
    """Minimal business process info for asset linking display."""
    id: UUID
    name: str
    status: str

    model_config = ConfigDict(from_attributes=True)


class AssetBase(BaseModel):
    """Shared fields for asset."""
    name: str = Field(..., min_length=1, max_length=255)
    asset_type: Optional[str] = None  # Can be old types or E-ITS types. If creating Target Object with target_type, this is optional
    description: Optional[str] = None
    remarks: Optional[str] = None
    criticality: Criticality = Criticality.NORMAL
    confidentiality_need: ProtectionNeedLevel = ProtectionNeedLevel.NORMAL
    integrity_need: ProtectionNeedLevel = ProtectionNeedLevel.NORMAL
    availability_need: ProtectionNeedLevel = ProtectionNeedLevel.NORMAL
    lifecycle_status: LifecycleStatus = LifecycleStatus.ACTIVE
    owner_user_id: Optional[UUID] = None
    person_id: Optional[UUID] = None
    is_grouped: bool = False
    quantity: int = 1
    group_name: Optional[str] = None


class AssetCreate(AssetBase):
    """Schema for creating an asset or target object."""
    target_type: Optional[str] = None  # E-ITS type (APP, SYS, NET, INF, IND) - overrides asset_type for Target Objects


class AssetUpdate(BaseModel):
    """Schema for updating an asset. All fields optional."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    asset_type: Optional[str] = None  # Can be old types or E-ITS types
    description: Optional[str] = None
    remarks: Optional[str] = None
    criticality: Optional[Criticality] = None
    confidentiality_need: Optional[ProtectionNeedLevel] = None
    integrity_need: Optional[ProtectionNeedLevel] = None
    availability_need: Optional[ProtectionNeedLevel] = None
    lifecycle_status: Optional[LifecycleStatus] = None
    owner_user_id: Optional[UUID] = None
    person_id: Optional[UUID] = None
    is_grouped: Optional[bool] = None
    quantity: Optional[int] = None
    group_name: Optional[str] = None
    target_type: Optional[TargetObjectType] = None  # Override asset_type for Target Objects


class AssetResponse(AssetBase):
    """Schema for asset response."""
    id: UUID
    tenant_id: UUID
    owner: Optional[OwnerInfo] = None
    linked_process_count: int = 0
    linked_processes: list[LinkedProcessInfo] = []
    can_manage_links: bool = False
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TargetObjectResponse(BaseModel):
    """Schema for Target Object response."""
    id: UUID
    tenant_id: UUID
    name: str
    asset_type: str  # E-ITS category (APP, SYS, NET, INF, IND)
    description: Optional[str] = None
    remarks: Optional[str] = None
    criticality: str
    is_grouped: bool = True
    quantity: int
    group_name: Optional[str] = None
    confidentiality_need: str
    integrity_need: str
    availability_need: str
    lifecycle_status: str
    owner_user_id: Optional[UUID] = None
    person_id: Optional[UUID] = None
    linked_process_count: int = 0
    module_mapping_count: int = 0
    imr_item_count: int = 0
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AssetListItem(BaseModel):
    """Simplified asset for list views."""
    id: UUID
    tenant_id: UUID
    name: str
    asset_type: str
    criticality: str
    confidentiality_need: str
    integrity_need: str
    availability_need: str
    lifecycle_status: str
    owner_user_id: Optional[UUID] = None
    person_id: Optional[UUID] = None
    owner: Optional[OwnerInfo] = None
    linked_process_count: int = 0
    linked_processes: list[LinkedProcessInfo] = []
    can_manage_links: bool = False
    created_at: datetime
    updated_at: Optional[datetime] = None
    remarks: Optional[str] = None
    is_grouped: bool = False
    quantity: int = 1
    group_name: Optional[str] = None
    module_mapping_count: int = 0

    model_config = ConfigDict(from_attributes=True)


class AssetLinkProcessRequest(BaseModel):
    """Schema for linking an asset to a business process."""
    pass