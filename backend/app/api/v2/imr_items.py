"""IMR Items API v2 - E-ITS implementation plan with PEARO."""
from typing import Optional, List
from uuid import UUID
from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func, distinct
from io import BytesIO

from app.api.deps import DB
from app.api.v2.auth import get_current_user_v2, LocalUser
from app.models.imr_item import ImrItem
from app.models.asset_module_mapping import AssetModuleMapping
from app.models.eits_catalog_measure import EitsCatalogMeasure
from app.models.eits_module import EitsModule
from app.models.asset import Asset
from app.models.evidence import Evidence
from app.models.evidence_link import EvidenceLink
from app.services.v2.imr_service import ImrService
from app.schemas.eits_catalog import (
    ImrItemCreate,
    ImrItemUpdate,
    ImrItemResponse,
    ImrSummaryResponse,
    AssetProtectionOverview,
)
from app.core.audit import log_audit as audit_log
from app.core.utils import active_query

router = APIRouter()


def _build_imr_response(db: Session, item: ImrItem, linked_asset_count: int = 0) -> ImrItemResponse:
    measure = db.query(EitsCatalogMeasure).filter(EitsCatalogMeasure.id == item.measure_id).first()
    module_group = None
    measure_info = None
    if measure and measure.module:
        module_group = measure.module.module_group
        measure_info = {
            "id": measure.id,
            "code": measure.code,
            "name": measure.name,
            "measure_level": measure.measure_level,
            "module_group": module_group,
        }
    elif measure:
        measure_info = {
            "id": measure.id,
            "code": measure.code,
            "name": measure.name,
            "measure_level": measure.measure_level,
            "module_group": None,
        }
    
    # Derive requirement_profile from measure level if not set
    profile = item.requirement_profile
    if not profile and measure:
        profile = "PÕHIMEEDE" if measure.measure_level == "BASE" else "PIIRATULT"
    
    return ImrItemResponse(
        id=item.id,
        tenant_id=item.tenant_id,
        asset_module_mapping_id=item.asset_module_mapping_id,
        is_process_module_measure=item.is_process_module_measure,
        measure_id=item.measure_id,
        pearo_status=item.pearo_status,
        implementation_description=item.implementation_description,
        non_implementation_justification=item.non_implementation_justification,
        partial_scope_description=item.partial_scope_description,
        responsible_user_id=item.responsible_user_id,
        due_date=item.due_date,
        next_review_date=item.next_review_date,
        priority=item.priority,
        risk_acceptance_approved_by=item.risk_acceptance_approved_by,
        risk_acceptance_date=item.risk_acceptance_date,
        verification_method=item.verification_method,
        last_verified_at=item.last_verified_at,
        created_at=item.created_at,
        updated_at=item.updated_at,
        measure=measure_info,
        mapped_module_id=item.mapped_module_id,
        created_by=item.created_by,
        updated_by=item.updated_by,
        status_changed_at=item.status_changed_at,
        requirement_profile=profile,
        todo_description=item.todo_description,
        cost_eur=float(item.cost_eur) if item.cost_eur else None,
        linked_asset_count=linked_asset_count,
    )


@router.get("/export")
def export_imr_to_excel(
    db: DB,
    current_user: LocalUser = Depends(get_current_user_v2),
    pearo_status: Optional[str] = Query(None, alias="pearo_status"),
    priority: Optional[str] = Query(None, alias="priority"),
    overdue_only: bool = Query(False, alias="overdue_only"),
):
    """Export IMR items as Excel file (filtered by current query params)."""
    excel_bytes = ImrService.export_imr_to_excel(
        db=db,
        tenant_id=current_user.tenant_id,
        pearo_status=pearo_status,
        priority=priority,
        overdue_only=overdue_only,
    )
    buffer = BytesIO(excel_bytes)
    buffer.seek(0)
    filename = f"IMR_{date.today().isoformat()}.xlsx"
    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/", response_model=list[ImrItemResponse])
def list_imr_items(
    db: DB,
    current_user: LocalUser = Depends(get_current_user_v2),
    pearo_status: Optional[str] = Query(None, alias="pearo_status"),
    priority: Optional[str] = Query(None, alias="priority"),
    asset_id: Optional[UUID] = Query(None, alias="asset_id"),
    overdue_only: bool = Query(False, alias="overdue_only"),
    module_group: Optional[str] = Query(None, alias="module_group"),
    snapshot_id: Optional[UUID] = Query(None, alias="snapshot_id"),
    skip: int = Query(0, ge=0),
    limit: int = Query(200, ge=1, le=500),
):
    """List IMR items for current tenant.

    By default returns only current items (imr_snapshot_id IS NULL).
    Pass snapshot_id to view items from a specific historical snapshot.
    """
    query = db.query(ImrItem).filter(ImrItem.tenant_id == current_user.tenant_id)
    query = active_query(query, ImrItem)
    if snapshot_id:
        query = query.filter(ImrItem.imr_snapshot_id == snapshot_id)
    else:
        query = query.filter(ImrItem.imr_snapshot_id.is_(None))
    if pearo_status:
        query = query.filter(ImrItem.pearo_status == pearo_status)
    if priority:
        query = query.filter(ImrItem.priority == priority)
    if asset_id:
        mapping_ids = db.query(AssetModuleMapping.id).filter(AssetModuleMapping.asset_id == asset_id).all()
        query = query.filter(ImrItem.asset_module_mapping_id.in_([m[0] for m in mapping_ids]))
    if overdue_only:
        query = query.filter(
            ImrItem.due_date < date.today(),
            ImrItem.pearo_status.in_(["E", "O"]),
        )
    if module_group:
        query = query.join(EitsCatalogMeasure, EitsCatalogMeasure.id == ImrItem.measure_id)
        query = query.join(EitsModule, EitsModule.id == EitsCatalogMeasure.module_id)
        query = query.filter(EitsModule.module_group == module_group)
    items = query.order_by(ImrItem.created_at.desc()).offset(skip).limit(limit).all()
    
    # Batch compute linked asset counts per measure
    measure_ids = list(set(item.measure_id for item in items))
    if measure_ids:
        counts = (
            db.query(
                ImrItem.measure_id,
                func.count(distinct(AssetModuleMapping.asset_id)).label("cnt")
            )
            .join(AssetModuleMapping, AssetModuleMapping.id == ImrItem.asset_module_mapping_id)
            .filter(
                ImrItem.measure_id.in_(measure_ids),
                ImrItem.tenant_id == current_user.tenant_id,
                ImrItem.asset_module_mapping_id.isnot(None),
            )
            .group_by(ImrItem.measure_id)
            .all()
        )
        count_map = {str(r.measure_id): r.cnt for r in counts}
    else:
        count_map = {}
    
    return [_build_imr_response(db, item, count_map.get(str(item.measure_id), 0)) for item in items]


@router.post("/", response_model=ImrItemResponse, status_code=status.HTTP_201_CREATED)
def create_imr_item(
    db: DB,
    current_user: LocalUser = Depends(get_current_user_v2),
    data: ImrItemCreate = None,
):
    """Create an IMR item."""
    if data is None:
        raise HTTPException(status_code=400, detail="Request body required")

    measure = db.query(EitsCatalogMeasure).filter(EitsCatalogMeasure.id == data.measure_id).first()
    if not measure:
        raise HTTPException(status_code=404, detail="Measure not found")

    if data.asset_module_mapping_id:
        mapping = db.query(AssetModuleMapping).filter(
            AssetModuleMapping.id == data.asset_module_mapping_id,
            AssetModuleMapping.tenant_id == current_user.tenant_id,
        ).first()
        if not mapping:
            raise HTTPException(status_code=404, detail="Asset-module mapping not found")

    item = ImrItem(
        tenant_id=current_user.tenant_id,
        asset_module_mapping_id=data.asset_module_mapping_id,
        measure_id=data.measure_id,
        is_process_module_measure=data.is_process_module_measure,
        pearo_status=data.pearo_status.value if hasattr(data.pearo_status, 'value') else data.pearo_status,
        implementation_description=data.implementation_description,
        non_implementation_justification=data.non_implementation_justification,
        partial_scope_description=data.partial_scope_description,
        responsible_user_id=data.responsible_user_id,
        due_date=data.due_date,
        next_review_date=data.next_review_date,
        priority=data.priority.value if hasattr(data.priority, 'value') else data.priority,
        verification_method=data.verification_method,
        requirement_profile=data.requirement_profile,
        todo_description=data.todo_description,
        cost_eur=data.cost_eur,
    )
    db.add(item)
    db.commit()
    db.refresh(item)

    audit_log(
        db=db,
        tenant_id=str(current_user.tenant_id),
        actor_user_id=str(current_user.global_user_id),
        action="create",
        entity_type="imr_item",
        entity_id=str(item.id),
        after_json={"measure_id": str(data.measure_id), "pearo_status": item.pearo_status},
    )

    return _build_imr_response(db, item)


@router.get("/{item_id}", response_model=ImrItemResponse)
def get_imr_item(
    item_id: UUID,
    db: DB,
    current_user: LocalUser = Depends(get_current_user_v2),
):
    """Get an IMR item by ID."""
    item = db.query(ImrItem).filter(
        ImrItem.id == item_id,
        ImrItem.tenant_id == current_user.tenant_id,
        ImrItem.deleted_at.is_(None),
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="IMR item not found")
    return _build_imr_response(db, item)


@router.patch("/{item_id}", response_model=ImrItemResponse)
def update_imr_item(
    item_id: UUID,
    db: DB,
    current_user: LocalUser = Depends(get_current_user_v2),
    data: ImrItemUpdate = None,
):
    """Update an IMR item (including PEARO status change)."""
    if data is None:
        raise HTTPException(status_code=400, detail="Request body required")

    item = db.query(ImrItem).filter(
        ImrItem.id == item_id,
        ImrItem.tenant_id == current_user.tenant_id,
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="IMR item not found")

    before = {"pearo_status": item.pearo_status, "priority": item.priority, "responsible_user_id": str(item.responsible_user_id) if item.responsible_user_id else None}

    update_data = data.model_dump(exclude_unset=True, exclude_none=True)
    
    new_status = update_data.get("pearo_status")
    
    # Track status changes
    if new_status and new_status != item.pearo_status:
        item.status_changed_at = datetime.utcnow()
    
    # Set updated_by
    item.updated_by = current_user.id
    
    for field, value in update_data.items():
        if hasattr(item, field):
            setattr(item, field, value)

    db.commit()
    db.refresh(item)
    
    audit_log(
        db=db,
        tenant_id=str(current_user.tenant_id),
        actor_user_id=str(current_user.global_user_id),
        action="update",
        entity_type="imr_item",
        entity_id=str(item.id),
        before_json=before,
        after_json={"pearo_status": item.pearo_status, "priority": item.priority},
    )

    return _build_imr_response(db, item)


@router.patch("/bulk-status")
def bulk_update_imr_status(
    db: DB,
    current_user: LocalUser = Depends(get_current_user_v2),
    item_ids: list[UUID] = None,
    pearo_status: str = None,
):
    """Bulk update PEARO status for multiple IMR items."""
    if not item_ids or not pearo_status:
        raise HTTPException(status_code=400, detail="item_ids and pearo_status required")

    items = db.query(ImrItem).filter(
        ImrItem.id.in_(item_ids),
        ImrItem.tenant_id == current_user.tenant_id,
    ).all()

    for item in items:
        item.pearo_status = pearo_status

    db.commit()

    audit_log(
        db=db,
        tenant_id=str(current_user.tenant_id),
        actor_user_id=str(current_user.global_user_id),
        action="bulk_update",
        entity_type="imr_item",
        entity_id="bulk",
        after_json={"item_count": len(items), "pearo_status": pearo_status},
    )

    return {"message": f"Updated {len(items)} items"}


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_imr_item(
    item_id: UUID,
    db: DB,
    current_user: LocalUser = Depends(get_current_user_v2),
):
    """Delete an IMR item."""
    item = db.query(ImrItem).filter(
        ImrItem.id == item_id,
        ImrItem.tenant_id == current_user.tenant_id,
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="IMR item not found")

    audit_log(
        db=db,
        tenant_id=str(current_user.tenant_id),
        actor_user_id=str(current_user.global_user_id),
        action="delete",
        entity_type="imr_item",
        entity_id=str(item_id),
    )

    item.soft_delete(current_user.global_user_id)
    db.commit()


@router.get("/reports/imr-summary", response_model=list[ImrSummaryResponse])
def get_imr_summary(
    db: DB,
    current_user: LocalUser = Depends(get_current_user_v2),
):
    """Get IMR summary statistics for current tenant."""
    from sqlalchemy import text
    result = db.execute(text("SELECT * FROM v_imr_summary WHERE tenant_id = :tid"), {"tid": str(current_user.tenant_id)})
    rows = result.fetchall()
    return [ImrSummaryResponse(
        tenant_id=row.tenant_id,
        pearo_status=row.pearo_status,
        measure_level=row.measure_level,
        measure_count=row.measure_count,
        overdue_count=row.overdue_count,
    ) for row in rows]


@router.get("/reports/asset-protection", response_model=list[AssetProtectionOverview])
def get_asset_protection_overview(
    db: DB,
    current_user: LocalUser = Depends(get_current_user_v2),
):
    """Get asset protection overview statistics."""
    from sqlalchemy import text
    result = db.execute(text("SELECT * FROM v_asset_protection_overview WHERE tenant_id = :tid"), {"tid": str(current_user.tenant_id)})
    rows = result.fetchall()
    return [AssetProtectionOverview(
        tenant_id=row.tenant_id,
        asset_id=row.asset_id,
        asset_index=row.asset_index,
        asset_name=row.asset_name,
        asset_category=row.asset_category,
        protection_need=row.protection_need or "NORMAL",
        mapped_module_count=row.mapped_module_count or 0,
        imr_item_count=row.imr_item_count or 0,
        implemented_count=row.implemented_count or 0,
        not_implemented_count=row.not_implemented_count or 0,
    ) for row in rows]


@router.post("/items/{item_id}/evidence", status_code=status.HTTP_201_CREATED)
def link_evidence_to_imr_item(
    item_id: UUID,
    db: DB,
    evidence_id: UUID = Query(..., description="Evidence ID to link"),
    current_user: LocalUser = Depends(get_current_user_v2),
):
    """Link evidence to an IMR item."""
    result = ImrService.link_evidence_to_imr(
        db=db,
        tenant_id=current_user.tenant_id,
        user_id=current_user.id,
        imr_item_id=item_id,
        evidence_id=evidence_id,
    )
    
    audit_log(
        db=db,
        tenant_id=str(current_user.tenant_id),
        actor_user_id=str(current_user.global_user_id),
        action="link_evidence",
        entity_type="imr_item",
        entity_id=str(item_id),
        after_json={"evidence_id": str(evidence_id)},
    )
    
    return result


@router.get("/items/{item_id}/validation", response_model=dict)
def get_imr_item_validation_status(
    item_id: UUID,
    db: DB,
    current_user: LocalUser = Depends(get_current_user_v2),
):
    """Get validation status for IMR item (can it transition to Implemented?)."""
    validation_data = ImrService.get_imr_item_with_validation_status(
        db=db,
        tenant_id=current_user.tenant_id,
        imr_item_id=item_id,
    )
    
    return {
        "can_transition_to_implemented": validation_data["can_transition_to_implemented"],
        "validation_errors": validation_data["validation_errors"],
        "linked_evidence_count": validation_data["linked_evidence_count"],
        "has_sufficient_implementation_details": validation_data["has_sufficient_implementation_details"],
        "imr_item_id": str(item_id),
        "current_status": validation_data["imr_item"].pearo_status if validation_data["imr_item"] else None
    }


@router.get("/reports/imr-summary-v2", response_model=dict)
def get_imr_summary_v2(
    db: DB,
    current_user: LocalUser = Depends(get_current_user_v2),
):
    """Get enhanced IMR summary statistics for dashboard."""
    return ImrService.get_imr_summary_statistics(
        db=db,
        tenant_id=current_user.tenant_id,
    )


@router.patch("/items/{item_id}/approve", response_model=ImrItemResponse)
def approve_imr_item_completion(
    item_id: UUID,
    db: DB,
    current_user: LocalUser = Depends(get_current_user_v2),
):
    """Approve IMR item completion (transition to Implemented status with validation)."""
    # First validate that it can transition to Implemented
    validation_data = ImrService.get_imr_item_with_validation_status(
        db=db,
        tenant_id=current_user.tenant_id,
        imr_item_id=item_id,
    )
    
    if not validation_data["can_transition_to_implemented"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="; ".join(validation_data["validation_errors"])
        )
    
    # Update the item to Implemented status
    item = db.query(ImrItem).filter(
        ImrItem.id == item_id,
        ImrItem.tenant_id == current_user.tenant_id,
    ).first()
    
    if not item:
        raise HTTPException(status_code=404, detail="IMR item not found")
    
    before_status = item.pearo_status
    item.pearo_status = "R"  # Implemented
    item.updated_by = current_user.id
    item.updated_at = datetime.datetime.utcnow()
    
    db.commit()
    db.refresh(item)
    
    audit_log(
        db=db,
        tenant_id=str(current_user.tenant_id),
        actor_user_id=str(current_user.global_user_id),
        action="approve_completion",
        entity_type="imr_item",
        entity_id=str(item_id),
        before_json={"pearo_status": before_status},
        after_json={"pearo_status": item.pearo_status},
    )
    
    return _build_imr_response(db, item)