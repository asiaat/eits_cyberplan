"""Business Process schemas."""
from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ProtectionNeedLevel(str, Enum):
    NORMAL = "normal"
    HIGH = "high"
    VERY_HIGH = "very_high"
    UNKNOWN = "unknown"


class BusinessProcessStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"


class AssetSummary(BaseModel):
    """Minimal asset info for nested display."""
    id: UUID
    name: str
    asset_type: str
    criticality: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class OwnerInfo(BaseModel):
    """Minimal user info for owner display."""
    id: UUID
    name: str
    email: str

    model_config = ConfigDict(from_attributes=True)


class ProcessAssetLink(BaseModel):
    """Link between business process and asset."""
    id: UUID
    asset_id: UUID
    asset: Optional[AssetSummary] = None
    relation_description: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class BusinessProcessBase(BaseModel):
    """Shared fields for business process."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    purpose: Optional[str] = None
    inputs: Optional[str] = None
    outputs: Optional[str] = None
    status: BusinessProcessStatus = BusinessProcessStatus.ACTIVE
    confidentiality_need: ProtectionNeedLevel = ProtectionNeedLevel.NORMAL
    integrity_need: ProtectionNeedLevel = ProtectionNeedLevel.NORMAL
    availability_need: ProtectionNeedLevel = ProtectionNeedLevel.NORMAL
    division_id: Optional[UUID] = None


class BusinessProcessCreate(BusinessProcessBase):
    """Schema for creating a business process."""
    owner_user_id: Optional[UUID] = None
    asset_ids: Optional[list[UUID]] = Field(default_factory=list, description="Asset IDs to link initially")


class BusinessProcessUpdate(BaseModel):
    """Schema for updating a business process. All fields optional."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    purpose: Optional[str] = None
    inputs: Optional[str] = None
    outputs: Optional[str] = None
    status: Optional[BusinessProcessStatus] = None
    confidentiality_need: Optional[ProtectionNeedLevel] = None
    integrity_need: Optional[ProtectionNeedLevel] = None
    availability_need: Optional[ProtectionNeedLevel] = None
    owner_user_id: Optional[UUID] = None


class BusinessProcessResponse(BusinessProcessBase):
    """Schema for business process response."""
    id: UUID
    tenant_id: UUID
    owner_user_id: Optional[UUID] = None
    owner: Optional[OwnerInfo] = None
    assets: list[ProcessAssetLink] = Field(default_factory=list)
    asset_count: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class BusinessProcessListItem(BaseModel):
    """Simplified business process for list views."""
    id: UUID
    tenant_id: UUID
    name: str
    status: BusinessProcessStatus
    confidentiality_need: ProtectionNeedLevel
    integrity_need: ProtectionNeedLevel
    availability_need: ProtectionNeedLevel
    division_id: Optional[UUID] = None
    owner: Optional[OwnerInfo] = None
    asset_count: int = 0
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProcessAssetLinkCreate(BaseModel):
    """Schema for linking an asset to a business process."""
    asset_id: UUID
    relation_description: Optional[str] = None


class ProcessAssetLinkUpdate(BaseModel):
    """Schema for updating an asset-process link."""
    relation_description: Optional[str] = None