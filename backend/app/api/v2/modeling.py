"""Scope Modeling API v2 - E-ITS modelleerimine."""
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.deps import DB
from app.api.v2.auth import get_current_user_v2, LocalUser
from app.models.bp_module_mapping import BusinessProcessModuleMapping
from app.models.eits_module import EitsModule
from app.models.business_process import BusinessProcess
from app.services.v2.modeling_service import ModelingService


class BpModuleMappingResponse(BaseModel):
    id: UUID
    business_process_id: UUID
    business_process_name: str
    module_id: UUID
    module_code: str
    module_name: str
    module_group: Optional[str] = None
    justification: Optional[str] = None
    modeled_by: Optional[UUID] = None
    modeled_at: Optional[str] = None

    model_config = {"from_attributes": True}


class BatchMapRequest(BaseModel):
    module_id: UUID
    target_ids: list[UUID]
    target_type: str = Field(pattern="^(asset|business_process)$")


class BatchMapResult(BaseModel):
    mapped: list[UUID] = Field(default_factory=list)
    skipped: list[dict] = Field(default_factory=list)
    errors: list[dict] = Field(default_factory=list)


router = APIRouter()


@router.post("/batch-map", status_code=status.HTTP_200_OK)
def batch_map_module(
    body: BatchMapRequest,
    db: DB = None,
    current_user: LocalUser = Depends(get_current_user_v2),
):
    """Map a module to multiple assets at once."""
    result = BatchMapResult()
    for target_id in body.target_ids:
        try:
            ModelingService.map_module_to_target(
                db=db,
                tenant_id=current_user.tenant_id,
                user_id=current_user.id,
                module_id=body.module_id,
                target_type=body.target_type,
                target_id=target_id,
            )
            result.mapped.append(target_id)
        except Exception as e:
            msg = str(e)
            if "not ready" in msg.lower() or "Cannot model" in msg:
                result.skipped.append({"id": str(target_id), "reason": msg})
            else:
                result.errors.append({"id": str(target_id), "reason": msg})
    return result


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


@router.get("/bp-mappings", response_model=list[BpModuleMappingResponse])
def list_bp_mappings(
    db: DB,
    current_user: LocalUser = Depends(get_current_user_v2),
):
    """List all BP-module mappings for the current tenant."""
    mappings = db.query(BusinessProcessModuleMapping).filter(
        BusinessProcessModuleMapping.tenant_id == current_user.tenant_id,
    ).all()

    result = []
    for m in mappings:
        bp = db.query(BusinessProcess).filter(BusinessProcess.id == m.business_process_id).first()
        mod = db.query(EitsModule).filter(EitsModule.id == m.module_id).first()
        result.append(BpModuleMappingResponse(
            id=m.id,
            business_process_id=m.business_process_id,
            business_process_name=bp.name if bp else "Unknown",
            module_id=m.module_id,
            module_code=mod.code if mod else "???",
            module_name=mod.name if mod else "Unknown",
            module_group=mod.module_group if mod else None,
            justification=m.justification,
            modeled_by=m.modeled_by,
            modeled_at=str(m.modeled_at) if m.modeled_at else None,
        ))

    return result


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
