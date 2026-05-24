from typing import Optional, List
from uuid import UUID
from datetime import datetime

from pydantic import BaseModel


class ImrSnapshotResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    protection_mode_selection_id: Optional[UUID] = None
    label: str
    description: Optional[str] = None
    is_current: bool
    item_count: int
    created_by: Optional[UUID] = None
    created_at: datetime
    restored_from: Optional[UUID] = None
    created_by_name: Optional[str] = None
    pm_approach: Optional[str] = None

    model_config = {"from_attributes": True}


class ImrSnapshotCreate(BaseModel):
    label: str
    description: Optional[str] = None
    protection_mode_selection_id: Optional[UUID] = None


class ImrSnapshotList(BaseModel):
    snapshots: List[ImrSnapshotResponse]
    total_count: int
