"""Targets API v2 - Target Objects (Sihtobjektid) management."""
from typing import Optional
from pydantic import BaseModel
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import DB
from app.api.v2.auth import get_current_user_v2, CurrentUserV2, LocalUser
from app.api.v2.auth import get_current_user_v2, CurrentUserV2, LocalUser
from app.models.asset import Asset
from app.models.asset_module_mapping import AssetModuleMapping
from app.models.eits_module import EitsModule
from app.models.eits_catalog_measure import EitsCatalogMeasure
from app.models.imr_item import ImrItem
from app.schemas.asset import (
    TargetObjectResponse,
    AssetCreate,
    AssetUpdate,
)
from app.core.audit import log_audit as audit_log

router = APIRouter()


def _determine_measure_levels(protection_need: str) -> list[str]:
    """
    Determine which E-ITS measure levels to include based on protection need.
    
    - NORMAL protection need: BASE + STANDARD measures only
    - HIGH or VERY_HIGH protection need: BASE + STANDARD + HIGH measures
    """
    if protection_need in ('HIGH', 'VERY_HIGH'):
        return ['BASE', 'STANDARD', 'HIGH']
    else:
        # NORMAL - include BASE and STANDARD only
        return ['BASE', 'STANDARD']


@router.get("/", response_model=list[TargetObjectResponse])
def list_targets(
    db: DB,
    current_user: LocalUser = CurrentUserV2,
    search: Optional[str] = Query(None, description="Search by name or group_name"),
):
    """List all Target Objects (grouped assets) for current tenant."""
    query = db.query(Asset).filter(
        Asset.tenant_id == current_user.tenant_id,
        Asset.is_grouped == True
    )
    
    if search:
        search_filter = f"%{search}%"
        query = query.filter(
            (Asset.name.ilike(search_filter)) | 
            (Asset.group_name.ilike(search_filter))
        )
    
    targets = query.order_by(Asset.name).all()
    
    result = []
    for target in targets:
        mapping_count = db.query(AssetModuleMapping).filter(
            AssetModuleMapping.asset_id == target.id,
            AssetModuleMapping.tenant_id == current_user.tenant_id
        ).count()
        
        imr_count = db.query(ImrItem).join(AssetModuleMapping).filter(
            AssetModuleMapping.asset_id == target.id,
            AssetModuleMapping.tenant_id == current_user.tenant_id
        ).count()
        
        target_dict = {
            "id": target.id,
            "tenant_id": target.tenant_id,
            "name": target.name,
            "asset_type": target.asset_type,
            "description": target.description,
            "remarks": target.remarks,
            "criticality": target.criticality,
            "is_grouped": target.is_grouped,
            "quantity": target.quantity,
            "group_name": target.group_name,
            "confidentiality_need": target.confidentiality_need,
            "integrity_need": target.integrity_need,
            "availability_need": target.availability_need,
            "lifecycle_status": target.lifecycle_status,
            "owner_user_id": target.owner_user_id,
            "person_id": target.person_id,
            "linked_process_count": 0,
            "module_mapping_count": mapping_count,
            "imr_item_count": imr_count,
            "created_at": target.created_at,
        }
        result.append(TargetObjectResponse(**target_dict))
    
    return result


@router.post("/", response_model=TargetObjectResponse, status_code=status.HTTP_201_CREATED)
def create_target(
    target_in: AssetCreate,
    db: DB,
    current_user: LocalUser = CurrentUserV2,
):
    """Create a new Target Object."""
    if not target_in.is_grouped and not target_in.target_type:
        raise HTTPException(
            status_code=400,
            detail="Target Objects must have is_grouped=True and target_type specified"
        )
    
    # If target_type is specified, use it as asset_type
    # Otherwise use asset_type if provided, or default to 'OTHER'
    if target_in.target_type:
        asset_type = target_in.target_type
    elif target_in.asset_type:
        asset_type = target_in.asset_type
    else:
        asset_type = "OTHER"
    
    target = Asset(
        tenant_id=current_user.tenant_id,
        name=target_in.name,
        asset_type=asset_type,
        description=target_in.description,
        remarks=target_in.remarks,
        criticality=target_in.criticality.value if hasattr(target_in.criticality, 'value') else target_in.criticality,
        confidentiality_need=target_in.confidentiality_need.value if hasattr(target_in.confidentiality_need, 'value') else target_in.confidentiality_need,
        integrity_need=target_in.integrity_need.value if hasattr(target_in.integrity_need, 'value') else target_in.integrity_need,
        availability_need=target_in.availability_need.value if hasattr(target_in.availability_need, 'value') else target_in.availability_need,
        lifecycle_status=target_in.lifecycle_status.value if hasattr(target_in.lifecycle_status, 'value') else target_in.lifecycle_status,
        owner_user_id=target_in.owner_user_id,
        person_id=target_in.person_id,
        is_grouped=True,
        quantity=target_in.quantity,
        group_name=target_in.group_name,
    )
    
    db.add(target)
    db.commit()
    db.refresh(target)
    
    # Audit log - temporarily disabled for testing
    # audit_log(
    #     db=db,
    #     tenant_id=current_user.tenant_id,
    #     actor_user_id=current_user.id,
    #     action="CREATE",
    #     entity_type="target_object",
    #     entity_id=str(target.id),
    #     after_json={"name": target.name, "asset_type": target.asset_type},
    # )
    pass
    
    return TargetObjectResponse(
        id=target.id,
        tenant_id=target.tenant_id,
        name=target.name,
        asset_type=target.asset_type,
        description=target.description,
        remarks=target.remarks,
        criticality=target.criticality,
        is_grouped=target.is_grouped,
        quantity=target.quantity,
        group_name=target.group_name,
        confidentiality_need=target.confidentiality_need,
        integrity_need=target.integrity_need,
        availability_need=target.availability_need,
        lifecycle_status=target.lifecycle_status,
        owner_user_id=target.owner_user_id,
        person_id=target.person_id,
        linked_process_count=0,
        module_mapping_count=0,
        imr_item_count=0,
        created_at=target.created_at,
    )


@router.get("/{target_id}", response_model=TargetObjectResponse)
def get_target(
    target_id: UUID,
    db: DB,
    current_user: LocalUser = CurrentUserV2,
):
    """Get a specific Target Object by ID."""
    target = db.query(Asset).filter(
        Asset.id == target_id,
        Asset.tenant_id == current_user.tenant_id,
        Asset.is_grouped == True
    ).first()
    
    if not target:
        raise HTTPException(status_code=404, detail="Target Object not found")
    
    mapping_count = db.query(AssetModuleMapping).filter(
        AssetModuleMapping.asset_id == target.id,
        AssetModuleMapping.tenant_id == current_user.tenant_id
    ).count()
    
    imr_count = db.query(ImrItem).join(AssetModuleMapping).filter(
        AssetModuleMapping.asset_id == target.id
    ).count()
    
    return TargetObjectResponse(
        id=target.id,
        tenant_id=target.tenant_id,
        name=target.name,
        asset_type=target.asset_type,
        description=target.description,
        remarks=target.remarks,
        criticality=target.criticality,
        is_grouped=target.is_grouped,
        quantity=target.quantity,
        group_name=target.group_name,
        confidentiality_need=target.confidentiality_need,
        integrity_need=target.integrity_need,
        availability_need=target.availability_need,
        lifecycle_status=target.lifecycle_status,
        owner_user_id=target.owner_user_id,
        person_id=target.person_id,
        linked_process_count=0,
        module_mapping_count=mapping_count,
        imr_item_count=imr_count,
        created_at=target.created_at,
    )


@router.put("/{target_id}", response_model=TargetObjectResponse)
def update_target(
    target_id: UUID,
    target_update: AssetUpdate,
    db: DB,
    current_user: LocalUser = CurrentUserV2,
):
    """Update a Target Object."""
    target = db.query(Asset).filter(
        Asset.id == target_id,
        Asset.tenant_id == current_user.tenant_id,
        Asset.is_grouped == True
    ).first()
    
    if not target:
        raise HTTPException(status_code=404, detail="Target Object not found")
    
    update_data = target_update.model_dump(exclude_unset=True)
    
    # Handle target_type override
    if 'target_type' in update_data and update_data['target_type']:
        update_data['asset_type'] = update_data['target_type'].value
        del update_data['target_type']
    
    # Convert enum values to strings
    for field in ['criticality', 'confidentiality_need', 'integrity_need', 'availability_need', 'lifecycle_status']:
        if field in update_data and update_data[field]:
            if hasattr(update_data[field], 'value'):
                update_data[field] = update_data[field].value
    
    for field, value in update_data.items():
        setattr(target, field, value)
    
    db.commit()
    db.refresh(target)
    
    # Audit log
    pass
    
    mapping_count = db.query(AssetModuleMapping).filter(
        AssetModuleMapping.asset_id == target.id,
        AssetModuleMapping.tenant_id == current_user.tenant_id
    ).count()
    
    imr_count = db.query(ImrItem).join(AssetModuleMapping).filter(
        AssetModuleMapping.asset_id == target.id
    ).count()
    
    return TargetObjectResponse(
        id=target.id,
        tenant_id=target.tenant_id,
        name=target.name,
        asset_type=target.asset_type,
        description=target.description,
        remarks=target.remarks,
        criticality=target.criticality,
        is_grouped=target.is_grouped,
        quantity=target.quantity,
        group_name=target.group_name,
        confidentiality_need=target.confidentiality_need,
        integrity_need=target.integrity_need,
        availability_need=target.availability_need,
        lifecycle_status=target.lifecycle_status,
        owner_user_id=target.owner_user_id,
        person_id=target.person_id,
        linked_process_count=0,
        module_mapping_count=mapping_count,
        imr_item_count=imr_count,
        created_at=target.created_at,
    )


@router.delete("/{target_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_target(
    target_id: UUID,
    db: DB,
    current_user: LocalUser = CurrentUserV2,
):
    """Delete a Target Object (cascades to module mappings and IMR items)."""
    target = db.query(Asset).filter(
        Asset.id == target_id,
        Asset.tenant_id == current_user.tenant_id,
        Asset.is_grouped == True
    ).first()
    
    if not target:
        raise HTTPException(status_code=404, detail="Target Object not found")
    
    target_name = target.name
    db.delete(target)
    db.commit()
    
    # Audit log
    pass


@router.get("/{target_id}/modules")
def get_target_modules(
    target_id: UUID,
    db: DB,
    current_user: LocalUser = CurrentUserV2,
):
    """Get all E-ITS module mappings for a Target Object."""
    target = db.query(Asset).filter(
        Asset.id == target_id,
        Asset.tenant_id == current_user.tenant_id,
        Asset.is_grouped == True
    ).first()
    
    if not target:
        raise HTTPException(status_code=404, detail="Target Object not found")
    
    mappings = db.query(AssetModuleMapping).filter(
        AssetModuleMapping.asset_id == target_id,
        AssetModuleMapping.tenant_id == current_user.tenant_id
    ).all()
    
    result = []
    for mapping in mappings:
        imr_items = db.query(ImrItem).filter(
            ImrItem.asset_module_mapping_id == mapping.id
        ).all()
        
        result.append({
            "id": str(mapping.id),
            "module_id": str(mapping.module_id),
            "module_code": mapping.module.code if mapping.module else None,
            "module_name": mapping.module.name if mapping.module else None,
            "module_group": mapping.module.module_group if mapping.module else None,
            "justification": mapping.justification,
            "modeled_by": str(mapping.modeled_by) if mapping.modeled_by else None,
            "modeled_at": mapping.modeled_at.isoformat() if mapping.modeled_at else None,
            "imr_item_count": len(imr_items),
            "imr_status_summary": _get_imr_status_summary(imr_items),
        })
    
    return result


def _get_imr_status_summary(imr_items: list[ImrItem]) -> dict:
    """Calculate IMR status summary from imr_items."""
    status_counts = {"P": 0, "E": 0, "A": 0, "R": 0, "O": 0}
    for item in imr_items:
        if item.pearo_status in status_counts:
            status_counts[item.pearo_status] += 1
    return status_counts


class TargetModuleAddRequest(BaseModel):
    """Schema for adding a module to a Target Object."""
    module_id: UUID
    justification: Optional[str] = None


@router.post("/{target_id}/modules", status_code=status.HTTP_201_CREATED)
def add_target_module(
    target_id: UUID,
    module_data: TargetModuleAddRequest,
    db: DB,
    current_user: LocalUser = CurrentUserV2,
):
    """
    Add E-ITS module mapping to a Target Object.
    
    ATOMIC OPERATION: Creates AssetModuleMapping AND generates ImrItem records
    in a single database transaction. If IMR generation fails, the mapping
    insert will rollback.
    """
    target = db.query(Asset).filter(
        Asset.id == target_id,
        Asset.tenant_id == current_user.tenant_id,
        Asset.is_grouped == True
    ).first()
    
    if not target:
        raise HTTPException(status_code=404, detail="Target Object not found")
    
    module = db.query(EitsModule).filter(
        EitsModule.id == module_data.module_id
    ).first()
    
    if not module:
        raise HTTPException(status_code=404, detail="E-ITS Module not found")
    
    # Check for existing mapping
    existing = db.query(AssetModuleMapping).filter(
        AssetModuleMapping.asset_id == target_id,
        AssetModuleMapping.module_id == module_data.module_id,
        AssetModuleMapping.tenant_id == current_user.tenant_id,
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Module already mapped to this Target Object")
    
    try:
        # 1. Create AssetModuleMapping
        mapping = AssetModuleMapping(
            tenant_id=current_user.tenant_id,
            asset_id=target_id,
            module_id=module_data.module_id,
            justification=module_data.justification,
            modeled_by=current_user.id,
        )
        db.add(mapping)
        db.flush()  # Get ID without committing
        
        # 2. Determine measure levels based on Target's protection need
        measure_levels = _determine_measure_levels(target.criticality)
        
        # 3. Query measures for the module at the appropriate level(s)
        measures = db.query(EitsCatalogMeasure).filter(
            EitsCatalogMeasure.module_id == module_data.module_id,
            EitsCatalogMeasure.measure_level.in_(measure_levels),
        ).all()
        
        # 4. Generate IMR items for each measure (inline, same transaction)
        items_created = []
        for measure in measures:
            imr_item = ImrItem(
                tenant_id=current_user.tenant_id,
                asset_module_mapping_id=mapping.id,
                measure_id=measure.id,
                pearo_status="E",  # Not Implemented (Ei ole rakendatud)
                priority="P2",
            )
            db.add(imr_item)
            items_created.append(imr_item)
        
        # 5. Commit the entire transaction (mapping + all IMR items)
        db.commit()
        
        for item in items_created:
            db.refresh(item)
        
        audit_log(
            db=db,
            user_id=current_user.id,
            action="CREATE",
            entity_type="target_module_mapping",
            entity_id=str(mapping.id),
            description=f"Mapped module {module.code} to Target {target.name} and generated {len(items_created)} IMR items",
        )
        
        return {
            "mapping_id": str(mapping.id),
            "module_code": module.code,
            "module_name": module.name,
            "measures_count": len(measures),
            "imr_items_created": len(items_created),
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create module mapping: {str(e)}"
        )


@router.delete("/{target_id}/modules/{mapping_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_target_module(
    target_id: UUID,
    mapping_id: UUID,
    db: DB,
    current_user: LocalUser = CurrentUserV2,
):
    """Remove an E-ITS module mapping from a Target Object (cascades to IMR items)."""
    target = db.query(Asset).filter(
        Asset.id == target_id,
        Asset.tenant_id == current_user.tenant_id,
        Asset.is_grouped == True
    ).first()
    
    if not target:
        raise HTTPException(status_code=404, detail="Target Object not found")
    
    mapping = db.query(AssetModuleMapping).filter(
        AssetModuleMapping.id == mapping_id,
        AssetModuleMapping.asset_id == target_id,
        AssetModuleMapping.tenant_id == current_user.tenant_id,
    ).first()
    
    if not mapping:
        raise HTTPException(status_code=404, detail="Module mapping not found")
    
    module_code = mapping.module.code if mapping.module else "Unknown"
    db.delete(mapping)
    db.commit()
    
    # Audit log
    pass


@router.get("/{target_id}/imr")
def get_target_imr(
    target_id: UUID,
    db: DB,
    current_user: LocalUser = CurrentUserV2,
):
    """Get all IMR items for a Target Object."""
    target = db.query(Asset).filter(
        Asset.id == target_id,
        Asset.tenant_id == current_user.tenant_id,
        Asset.is_grouped == True
    ).first()
    
    if not target:
        raise HTTPException(status_code=404, detail="Target Object not found")
    
    mappings = db.query(AssetModuleMapping).filter(
        AssetModuleMapping.asset_id == target_id,
        AssetModuleMapping.tenant_id == current_user.tenant_id
    ).all()
    
    mapping_ids = [m.id for m in mappings]
    
    if not mapping_ids:
        return []
    
    imr_items = db.query(ImrItem).filter(
        ImrItem.asset_module_mapping_id.in_(mapping_ids)
    ).all()
    
    result = []
    for item in imr_items:
        mapping = next((m for m in mappings if m.id == item.asset_module_mapping_id), None)
        result.append({
            "id": str(item.id),
            "measure_code": item.measure.code if item.measure else None,
            "measure_name": item.measure.name if item.measure else None,
            "measure_level": item.measure.measure_level if item.measure else None,
            "module_code": mapping.module.code if mapping and mapping.module else None,
            "module_name": mapping.module.name if mapping and mapping.module else None,
            "pearo_status": item.pearo_status,
            "priority": item.priority,
            "assigned_to": str(item.assigned_to) if item.assigned_to else None,
            "deadline": item.deadline.isoformat() if item.deadline else None,
            "comments": item.comments,
            "updated_at": item.updated_at.isoformat() if item.updated_at else None,
        })
    
    return result
