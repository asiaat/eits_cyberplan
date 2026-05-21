"""Scope Modeling API v2 - E-ITS modelleerimine."""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.deps import DB
from app.api.v2.auth import get_current_user_v2, LocalUser
from app.services.v2.modeling_service import ModelingService

router = APIRouter()


@router.post("/map", status_code=status.HTTP_201_CREATED)
def map_module(
    module_id: UUID = Query(..., description="E-ITS module ID"),
    target_type: str = Query(..., pattern="^(asset|business_process)$", description="'asset' or 'business_process'"),
    target_id: UUID = Query(..., description="Asset or business process ID"),
    db: DB = None,
    current_user: LocalUser = Depends(get_current_user_v2),
):
    """Map an E-ITS module to an asset or business process and auto-generate IMR items."""
    return ModelingService.map_module_to_target(
        db=db,
        tenant_id=current_user.tenant_id,
        user_id=current_user.id,
        module_id=module_id,
        target_type=target_type,
        target_id=target_id,
    )


@router.delete("/map/{mapping_id}", status_code=status.HTTP_200_OK)
def unmap_module(
    mapping_id: UUID,
    target_type: str = Query(..., pattern="^(asset|business_process)$", description="'asset' or 'business_process'"),
    db: DB = None,
    current_user: LocalUser = Depends(get_current_user_v2),
):
    """Remove a module from scope and delete its Planned IMR items."""
    return ModelingService.remove_module_from_target(
        db=db,
        tenant_id=current_user.tenant_id,
        mapping_id=mapping_id,
        target_type=target_type,
    )


@router.patch("/business-process/{process_id}/protection-need", status_code=status.HTTP_200_OK)
def update_process_protection_need(
    process_id: UUID,
    confidentiality: str = Query(..., description="Confidentiality need (normal/high/very_high)"),
    integrity: str = Query(..., description="Integrity need (normal/high/very_high)"),
    availability: str = Query(..., description="Availability need (normal/high/very_high)"),
    db: DB = None,
    current_user: LocalUser = Depends(get_current_user_v2),
):
    """Update business process protection needs. Locked when protection mode is active."""
    return ModelingService.update_process_protection_need(
        db=db,
        tenant_id=current_user.tenant_id,
        process_id=process_id,
        confidentiality=confidentiality,
        integrity=integrity,
        availability=availability,
    )
