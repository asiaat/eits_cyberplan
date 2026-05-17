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
    asset_type: AssetType
    description: Optional[str] = None
    remarks: Optional[str] = None
    criticality: Criticality = Criticality.NORMAL
    confidentiality_need: ProtectionNeedLevel = ProtectionNeedLevel.NORMAL
    integrity_need: ProtectionNeedLevel = ProtectionNeedLevel.NORMAL
    availability_need: ProtectionNeedLevel = ProtectionNeedLevel.NORMAL
    lifecycle_status: LifecycleStatus = LifecycleStatus.ACTIVE
    owner_user_id: Optional[UUID] = None
    person_id: Optional[UUID] = None


class AssetCreate(AssetBase):
    """Schema for creating an asset."""
    pass


class AssetUpdate(BaseModel):
    """Schema for updating an asset. All fields optional."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    asset_type: Optional[AssetType] = None
    description: Optional[str] = None
    remarks: Optional[str] = None
    criticality: Optional[Criticality] = None
    confidentiality_need: Optional[ProtectionNeedLevel] = None
    integrity_need: Optional[ProtectionNeedLevel] = None
    availability_need: Optional[ProtectionNeedLevel] = None
    lifecycle_status: Optional[LifecycleStatus] = None
    owner_user_id: Optional[UUID] = None
    person_id: Optional[UUID] = None


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


class AssetListItem(BaseModel):
    """Simplified asset for list views."""
    id: UUID
    tenant_id: UUID
    name: str
    asset_type: AssetType
    criticality: Criticality
    confidentiality_need: ProtectionNeedLevel
    integrity_need: ProtectionNeedLevel
    availability_need: ProtectionNeedLevel
    lifecycle_status: LifecycleStatus
    owner_user_id: Optional[UUID] = None
    person_id: Optional[UUID] = None
    owner: Optional[OwnerInfo] = None
    linked_process_count: int = 0
    linked_processes: list[LinkedProcessInfo] = []
    can_manage_links: bool = False
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AssetLinkProcessRequest(BaseModel):
    """Schema for linking an asset to a business process."""
    pass