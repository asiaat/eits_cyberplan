"""Asset Module Mappings API v2 - E-ITS modelleerimine."""
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import DB
from app.api.v2.auth import get_current_user_v2, LocalUser
from app.models.asset_module_mapping import AssetModuleMapping
from app.models.asset import Asset
from app.models.eits_module import EitsModule
from app.models.eits_catalog_measure import EitsCatalogMeasure
from app.models.imr_item import ImrItem
from app.models.process_asset import ProcessAsset
from app.models.security_profile import SecurityProfile
from app.services.v2.modeling_service import ModelingService
from app.schemas.eits_catalog import (
    AssetModuleMappingCreate,
    AssetModuleMappingUpdate,
    AssetModuleMappingResponse,
    ImrItemCreate,
    ImrItemResponse,
)
from app.core.audit import log_audit as audit_log

router = APIRouter()


def _build_mapping_response(db: Session, mapping: AssetModuleMapping) -> AssetModuleMappingResponse:
    module = db.query(EitsModule).filter(EitsModule.id == mapping.module_id).first()
    return AssetModuleMappingResponse(
        id=mapping.id,
        tenant_id=mapping.tenant_id,
        asset_id=mapping.asset_id,
        module_id=mapping.module_id,
        justification=mapping.justification,
        modeled_by=mapping.modeled_by,
        modeled_at=mapping.modeled_at,
        module={"id": module.id, "code": module.code, "name": module.name, "module_group": module.module_group} if module else None,
    )


@router.get("/", response_model=list[AssetModuleMappingResponse])
def list_asset_module_mappings(
    db: DB,
    current_user: LocalUser = Depends(get_current_user_v2),
    asset_id: Optional[UUID] = Query(None, alias="asset_id"),
    module_group: Optional[str] = Query(None, alias="module_group"),
    skip: int = Query(0, ge=0),
    limit: int = Query(200, ge=1, le=500),
):
    """List asset-module mappings for current tenant."""
    query = db.query(AssetModuleMapping).filter(AssetModuleMapping.tenant_id == current_user.tenant_id)
    if asset_id:
        query = query.filter(AssetModuleMapping.asset_id == asset_id)
    if module_group:
        query = query.join(EitsModule).filter(EitsModule.module_group == module_group)
    mappings = query.offset(skip).limit(limit).all()
    return [_build_mapping_response(db, m) for m in mappings]


@router.post("/", response_model=AssetModuleMappingResponse, status_code=status.HTTP_201_CREATED)
def create_asset_module_mapping(
    db: DB,
    current_user: LocalUser = Depends(get_current_user_v2),
    data: AssetModuleMappingCreate = None,
):
    """Create an asset-module mapping (E-ITS modelleerimine)."""
    if data is None:
        raise HTTPException(status_code=400, detail="Request body required")

    asset = db.query(Asset).filter(
        Asset.id == data.asset_id,
        Asset.tenant_id == current_user.tenant_id,
    ).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    # CRITICAL: E-ITS lifecycle validation
    # Asset must be linked to a BP with an approved protection need before modeling is allowed
    ModelingService.validate_asset_ready_for_modeling(db, current_user.tenant_id, data.asset_id)

    module = db.query(EitsModule).filter(EitsModule.id == data.module_id).first()
    if not module:
        raise HTTPException(status_code=404, detail="Module not found")

    existing = db.query(AssetModuleMapping).filter(
        AssetModuleMapping.tenant_id == current_user.tenant_id,
        AssetModuleMapping.asset_id == data.asset_id,
        AssetModuleMapping.module_id == data.module_id,
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Mapping already exists")

    mapping = AssetModuleMapping(
        tenant_id=current_user.tenant_id,
        asset_id=data.asset_id,
        module_id=data.module_id,
        justification=data.justification,
        modeled_by=current_user.id,
    )
    db.add(mapping)
    db.commit()
    db.refresh(mapping)

    audit_log(
        db=db,
        tenant_id=str(current_user.tenant_id),
        actor_user_id=str(current_user.global_user_id),
        action="create",
        entity_type="asset_module_mapping",
        entity_id=str(mapping.id),
        after_json={"asset_id": str(data.asset_id), "module_id": str(data.module_id)},
    )

    return _build_mapping_response(db, mapping)


@router.get("/{mapping_id}", response_model=AssetModuleMappingResponse)
def get_asset_module_mapping(
    mapping_id: UUID,
    db: DB,
    current_user: LocalUser = Depends(get_current_user_v2),
):
    """Get an asset-module mapping by ID."""
    mapping = db.query(AssetModuleMapping).filter(
        AssetModuleMapping.id == mapping_id,
        AssetModuleMapping.tenant_id == current_user.tenant_id,
    ).first()
    if not mapping:
        raise HTTPException(status_code=404, detail="Mapping not found")
    return _build_mapping_response(db, mapping)


@router.patch("/{mapping_id}", response_model=AssetModuleMappingResponse)
def update_asset_module_mapping(
    mapping_id: UUID,
    db: DB,
    current_user: LocalUser = Depends(get_current_user_v2),
    data: AssetModuleMappingUpdate = None,
):
    """Update an asset-module mapping."""
    if data is None:
        raise HTTPException(status_code=400, detail="Request body required")

    mapping = db.query(AssetModuleMapping).filter(
        AssetModuleMapping.id == mapping_id,
        AssetModuleMapping.tenant_id == current_user.tenant_id,
    ).first()
    if not mapping:
        raise HTTPException(status_code=404, detail="Mapping not found")

    if data.justification is not None:
        mapping.justification = data.justification

    db.commit()
    db.refresh(mapping)
    return _build_mapping_response(db, mapping)


@router.delete("/{mapping_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_asset_module_mapping(
    mapping_id: UUID,
    db: DB,
    current_user: LocalUser = Depends(get_current_user_v2),
):
    """Delete an asset-module mapping."""
    mapping = db.query(AssetModuleMapping).filter(
        AssetModuleMapping.id == mapping_id,
        AssetModuleMapping.tenant_id == current_user.tenant_id,
    ).first()
    if not mapping:
        raise HTTPException(status_code=404, detail="Mapping not found")

    imr_items = db.query(ImrItem).filter(
        ImrItem.asset_module_mapping_id == mapping_id
    ).all()
    for item in imr_items:
        item.soft_delete(current_user.global_user_id)
        item.asset_module_mapping_id = None

    audit_log(
        db=db,
        tenant_id=str(current_user.tenant_id),
        actor_user_id=str(current_user.global_user_id),
        action="delete",
        entity_type="asset_module_mapping",
        entity_id=str(mapping_id),
        before_json={"asset_id": str(mapping.asset_id), "module_id": str(mapping.module_id)},
    )

    db.delete(mapping)
    db.commit()


@router.post("/generate-imr", response_model=list[ImrItemResponse], status_code=status.HTTP_201_CREATED)
def generate_imr_from_mappings(
    db: DB,
    current_user: LocalUser = Depends(get_current_user_v2),
    asset_id: Optional[UUID] = Query(None, alias="asset_id"),
):
    """Generate IMR items from asset-module mappings.
    
    For CORE mode:
    - Assets marked as is_core=True get BASE + STANDARD measures (PÕHIMEEDE + PIIRATULT)
    - Assets not marked as core get only BASE measures (PÕHIMEEDE only)
    """
    if asset_id:
        mappings = db.query(AssetModuleMapping).filter(
            AssetModuleMapping.tenant_id == current_user.tenant_id,
            AssetModuleMapping.asset_id == asset_id,
        ).all()
    else:
        mappings = db.query(AssetModuleMapping).filter(
            AssetModuleMapping.tenant_id == current_user.tenant_id,
        ).all()

    security_profile = db.query(SecurityProfile).filter(
        SecurityProfile.tenant_id == current_user.tenant_id,
    ).order_by(SecurityProfile.created_at.desc()).first()

    approach = security_profile.security_approach if security_profile else "BASIC"
    level_filter = {"BASIC": ["BASE"], "STANDARD": ["BASE", "STANDARD"], "CORE": ["BASE", "STANDARD"]}[approach]

    items_created = []
    for mapping in mappings:
        # For CORE mode, filter by asset is_core status
        if approach == "CORE":
            asset = db.query(Asset).filter(Asset.id == mapping.asset_id).first()
            if asset and not asset.is_core:
                # Non-core assets in CORE mode only get BASE measures
                level_filter = ["BASE"]
            else:
                # Core assets get BASE + STANDARD
                level_filter = ["BASE", "STANDARD"]
        
        measures = db.query(EitsCatalogMeasure).filter(
            EitsCatalogMeasure.module_id == mapping.module_id,
            EitsCatalogMeasure.measure_level.in_(level_filter),
        ).all()

        for measure in measures:
            existing = db.query(ImrItem).filter(
                ImrItem.asset_module_mapping_id == mapping.id,
                ImrItem.measure_id == measure.id,
            ).first()
            if existing:
                continue

            item = ImrItem(
                tenant_id=current_user.tenant_id,
                asset_module_mapping_id=mapping.id,
                measure_id=measure.id,
                pearo_status="E",
                priority="P2",
                requirement_profile="PÕHIMEEDE" if measure.measure_level == "BASE" else "PIIRATULT",
            )
            db.add(item)
            items_created.append(item)

    db.commit()
    for item in items_created:
        db.refresh(item)

    return items_created