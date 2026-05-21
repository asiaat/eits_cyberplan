"""Business Processes API v2 - uses LocalUser/GlobalUser auth."""
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status, Header
from sqlalchemy.orm import Session

from app.api.deps import DB
from app.api.v2.auth import get_current_user_v2, CurrentUserV2, LocalUser
from app.models.asset import Asset
from app.models.process_asset import ProcessAsset
from app.models.business_process import BusinessProcess
from app.models.user import User
from app.models.business_process_dependency import BusinessProcessDependency
from app.schemas.business_process import (
    BusinessProcessCreate,
    BusinessProcessUpdate,
    BusinessProcessResponse,
    BusinessProcessListItem,
    ProcessAssetLinkCreate,
    BusinessProcessDependencyCreate,
    BusinessProcessDependencyResponse,
    BusinessProcessWithDependencies,
    BusinessProcessSummary,
)
from app.services.business_process_service import (
    calculate_protection_need,
    is_high_or_very_high,
    get_linked_asset_ids,
    create_cascade_alert,
    check_circular_dependency,
    get_upstream_dependencies,
    get_downstream_dependents,
    build_dependency_tree,
)
from app.core.audit import log_audit as audit_log
from app.models.protectionmode_selection import ProtectionModeSelection

router = APIRouter()


@router.get("/", response_model=list[BusinessProcessListItem])
def list_business_processes_v2(
    db: DB,
    current_user: LocalUser = CurrentUserV2,
    status_filter: Optional[str] = Query(None, alias="status"),
    owner_id: Optional[UUID] = Query(None, alias="owner_id"),
    division_id: Optional[str] = Query(None, alias="division_id"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
):
    """List business processes for the current tenant."""
    query = db.query(BusinessProcess).filter(
        BusinessProcess.tenant_id == current_user.tenant_id
    )

    if status_filter:
        query = query.filter(BusinessProcess.status == status_filter)
    if owner_id:
        query = query.filter(BusinessProcess.owner_user_id == owner_id)
    if division_id:
        query = query.filter(BusinessProcess.division_id == division_id)

    processes = query.order_by(BusinessProcess.created_at.desc()).offset(skip).limit(limit).all()

    result = []
    for bp in processes:
        owner = None
        if bp.owner_user_id:
            # Try old User model first
            user = db.query(User).filter(User.id == bp.owner_user_id).first()
            if user:
                owner = {"id": user.id, "name": user.name, "email": getattr(user, 'email', '') or getattr(user, 'name', '')}
            else:
                # Fall back to LocalUser
                local_user = db.query(LocalUser).filter(LocalUser.id == bp.owner_user_id).first()
                if local_user:
                    owner = {"id": str(local_user.id), "name": local_user.full_name, "email": ""}

        asset_count = db.query(ProcessAsset).filter(
            ProcessAsset.business_process_id == bp.id
        ).count()

        item = BusinessProcessListItem(
            id=bp.id,
            tenant_id=bp.tenant_id,
            name=bp.name,
            status=bp.status,
            confidentiality_need=bp.confidentiality_need,
            integrity_need=bp.integrity_need,
            availability_need=bp.availability_need,
            division_id=bp.division_id,
            owner=owner,
            asset_count=asset_count,
            created_at=bp.created_at,
        )
        result.append(item)

    return result


@router.post("", response_model=BusinessProcessResponse, status_code=status.HTTP_201_CREATED)
def create_business_process_v2(
    db: DB,
    current_user: LocalUser = CurrentUserV2,
    data: BusinessProcessCreate = None,
):
    """Create a new business process.

    SOP 1: Protection need is auto-calculated as MAX(C, I, A).
    SOP 2: HIGH/VERY_HIGH protection needs require justification and approval.
    SOP 3: HIGH/VERY_HIGH protection needs trigger cascade alerts for asset review.
    """
    if data is None:
        raise HTTPException(status_code=400, detail="Request body required")

    confidentiality = data.confidentiality_need.value if hasattr(data.confidentiality_need, 'value') else data.confidentiality_need
    integrity = data.integrity_need.value if hasattr(data.integrity_need, 'value') else data.integrity_need
    availability = data.availability_need.value if hasattr(data.availability_need, 'value') else data.availability_need

    protection_need = calculate_protection_need(confidentiality, integrity, availability)

    bp = BusinessProcess(
        tenant_id=current_user.tenant_id,
        name=data.name,
        description=data.description,
        purpose=data.purpose,
        inputs=data.inputs,
        outputs=data.outputs,
        status=data.status.value if hasattr(data.status, 'value') else data.status,
        confidentiality_need=confidentiality,
        integrity_need=integrity,
        availability_need=availability,
        division_id=data.division_id,
        owner_user_id=data.owner_user_id,
    )
    db.add(bp)
    db.flush()

    for asset_id in (data.asset_ids or []):
        asset = db.query(Asset).filter(
            Asset.id == asset_id,
            Asset.tenant_id == current_user.tenant_id
        ).first()
        if not asset:
            db.rollback()
            raise HTTPException(status_code=404, detail=f"Asset {asset_id} not found")
        link = ProcessAsset(
            tenant_id=current_user.tenant_id,
            business_process_id=bp.id,
            asset_id=asset_id,
        )
        db.add(link)

    if is_high_or_very_high(protection_need):
        linked_asset_ids = get_linked_asset_ids(db, bp.id)
        create_cascade_alert(
            db, current_user.tenant_id, bp.id, bp.name, protection_need, linked_asset_ids
        )

    db.commit()
    db.refresh(bp)

    import json
    audit_log(
        db=db,
        tenant_id=str(current_user.tenant_id),
        actor_user_id=str(current_user.global_user_id),
        action="create",
        entity_type="business_process",
        entity_id=str(bp.id),
        after_json={"business_process": bp.name},
    )

    return _build_response(db, bp)


@router.get("/{process_id}", response_model=BusinessProcessResponse)
def get_business_process_v2(
    db: DB,
    current_user: LocalUser = CurrentUserV2,
    process_id: UUID = None,
):
    """Get a business process by ID."""
    if process_id is None or (isinstance(process_id, str) and process_id == "undefined"):
        raise HTTPException(status_code=400, detail="process_id is required")
    bp = db.query(BusinessProcess).filter(
        BusinessProcess.id == process_id,
        BusinessProcess.tenant_id == current_user.tenant_id,
    ).first()

    if not bp:
        raise HTTPException(status_code=404, detail="Business process not found")

    return _build_response(db, bp)


@router.patch("/{process_id}", response_model=BusinessProcessResponse)
def update_business_process_v2(
    db: DB,
    current_user: LocalUser = CurrentUserV2,
    process_id: UUID = None,
    data: BusinessProcessUpdate = None,
):
    """Update a business process."""
    if process_id is None:
        raise HTTPException(status_code=400, detail="process_id is required")
    if data is None:
        raise HTTPException(status_code=400, detail="Request body required")
    
    bp = db.query(BusinessProcess).filter(
        BusinessProcess.id == process_id,
        BusinessProcess.tenant_id == current_user.tenant_id,
    ).first()

    if not bp:
        raise HTTPException(status_code=404, detail="Business process not found")

    # Lockout: block C-I-A changes when protection mode is active
    needs_changing = any(
        getattr(data, f, None) is not None
        for f in ("confidentiality_need", "integrity_need", "availability_need")
    )
    if needs_changing:
        active = db.query(ProtectionModeSelection).filter(
            ProtectionModeSelection.tenant_id == current_user.tenant_id,
            ProtectionModeSelection.is_active == True,
        ).first()
        if active:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot modify protection needs when mode of protection ({active.security_approach}) has been set. Deactivate the protection mode first.",
            )

    before = {
        "name": bp.name,
        "description": bp.description,
        "status": bp.status,
        "confidentiality_need": bp.confidentiality_need,
        "integrity_need": bp.integrity_need,
        "availability_need": bp.availability_need,
    }

    old_protection_need = calculate_protection_need(
        bp.confidentiality_need,
        bp.integrity_need,
        bp.availability_need
    )

    update_data = data.model_dump(exclude_unset=True, exclude_none=True)
    for field, value in update_data.items():
        if field in ("status", "confidentiality_need", "integrity_need", "availability_need"):
            if hasattr(value, "value"):
                setattr(bp, field, value.value)
            else:
                setattr(bp, field, value)
        elif field == "owner_user_id":
            setattr(bp, field, value)
        elif field not in ("asset_ids", "justification", "approved_by"):
            setattr(bp, field, value)

    new_protection_need = calculate_protection_need(
        bp.confidentiality_need,
        bp.integrity_need,
        bp.availability_need
    )

    if is_high_or_very_high(new_protection_need) and new_protection_need != old_protection_need:
        linked_asset_ids = get_linked_asset_ids(db, bp.id)
        create_cascade_alert(
            db, current_user.tenant_id, bp.id, bp.name, new_protection_need, linked_asset_ids
        )

    db.commit()
    db.refresh(bp)

    audit_log(
        db=db,
        tenant_id=str(current_user.tenant_id),
        actor_user_id=str(current_user.global_user_id),
        action="update",
        entity_type="business_process",
        entity_id=str(bp.id),
        before_json=before,
        after_json={"business_process": bp.name},
    )

    return _build_response(db, bp)


@router.delete("/{process_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_business_process_v2(
    db: DB,
    current_user: LocalUser = CurrentUserV2,
    process_id: UUID = None,
):
    """Delete a business process."""
    if process_id is None:
        raise HTTPException(status_code=400, detail="process_id is required")
    
    bp = db.query(BusinessProcess).filter(
        BusinessProcess.id == process_id,
        BusinessProcess.tenant_id == current_user.tenant_id,
    ).first()

    if not bp:
        raise HTTPException(status_code=404, detail="Business process not found")

    db.query(ProcessAsset).filter(
        ProcessAsset.business_process_id == process_id
    ).delete()

    audit_log(
        db=db,
        tenant_id=str(current_user.tenant_id),
        actor_user_id=str(current_user.global_user_id),
        action="delete",
        entity_type="business_process",
        entity_id=str(bp.id),
        before_json={"business_process": bp.name},
    )

    db.delete(bp)
    db.commit()


@router.get("/{process_id}/dependencies", response_model=BusinessProcessWithDependencies)
def get_business_process_dependencies(
    db: DB,
    current_user: LocalUser = CurrentUserV2,
    process_id: UUID = None,
):
    """Get all dependencies (upstream and downstream) for a business process."""
    if process_id is None:
        raise HTTPException(status_code=400, detail="process_id is required")

    bp = db.query(BusinessProcess).filter(
        BusinessProcess.id == process_id,
        BusinessProcess.tenant_id == current_user.tenant_id,
    ).first()

    if not bp:
        raise HTTPException(status_code=404, detail="Business process not found")

    base_response = _build_response(db, bp)

    upstream_deps = get_upstream_dependencies(db, current_user.tenant_id, process_id)
    downstream_deps = get_downstream_dependents(db, current_user.tenant_id, process_id)

    upstream_list = []
    for dep in upstream_deps:
        dep_bp = db.query(BusinessProcess).filter(BusinessProcess.id == dep.depends_on_process_id).first()
        bp_summary = None
        if dep_bp:
            bp_summary = BusinessProcessSummary(
                id=dep_bp.id,
                name=dep_bp.name,
                status=dep_bp.status,
                confidentiality_need=dep_bp.confidentiality_need,
                integrity_need=dep_bp.integrity_need,
                availability_need=dep_bp.availability_need,
            )
        upstream_list.append({
            "id": dep.id,
            "depends_on_process_id": dep.depends_on_process_id,
            "dependency_type": dep.dependency_type,
            "description": dep.description,
            "created_at": dep.created_at,
            "depends_on_process": bp_summary,
        })

    downstream_list = []
    for dep in downstream_deps:
        dep_bp = db.query(BusinessProcess).filter(BusinessProcess.id == dep.primary_process_id).first()
        bp_summary = None
        if dep_bp:
            bp_summary = BusinessProcessSummary(
                id=dep_bp.id,
                name=dep_bp.name,
                status=dep_bp.status,
                confidentiality_need=dep_bp.confidentiality_need,
                integrity_need=dep_bp.integrity_need,
                availability_need=dep_bp.availability_need,
            )
        downstream_list.append({
            "id": dep.id,
            "depends_on_process_id": dep.primary_process_id,
            "dependency_type": dep.dependency_type,
            "description": dep.description,
            "created_at": dep.created_at,
            "depends_on_process": bp_summary,
        })

    return BusinessProcessWithDependencies(
        **base_response.model_dump(),
        dependencies=upstream_list,
        dependents=downstream_list,
    )


@router.post("/{process_id}/dependencies", response_model=BusinessProcessDependencyResponse, status_code=status.HTTP_201_CREATED)
def create_business_process_dependency(
    db: DB,
    current_user: LocalUser = CurrentUserV2,
    process_id: UUID = None,
    data: BusinessProcessDependencyCreate = None,
):
    """Create a dependency from one business process to another.

    Validates:
    - No self-referencing dependencies
    - No circular dependency chains
    - Both processes exist in the same tenant
    """
    if process_id is None:
        raise HTTPException(status_code=400, detail="process_id is required")
    if data is None:
        raise HTTPException(status_code=400, detail="Request body required")

    if process_id == data.depends_on_process_id:
        raise HTTPException(status_code=400, detail="A process cannot depend on itself")

    bp = db.query(BusinessProcess).filter(
        BusinessProcess.id == process_id,
        BusinessProcess.tenant_id == current_user.tenant_id,
    ).first()
    if not bp:
        raise HTTPException(status_code=404, detail="Business process not found")

    depends_on_bp = db.query(BusinessProcess).filter(
        BusinessProcess.id == data.depends_on_process_id,
        BusinessProcess.tenant_id == current_user.tenant_id,
    ).first()
    if not depends_on_bp:
        raise HTTPException(status_code=404, detail="Target process not found in this tenant")

    would_cycle, cycle_msg = check_circular_dependency(
        db, current_user.tenant_id, process_id, data.depends_on_process_id
    )
    if would_cycle:
        raise HTTPException(status_code=400, detail=cycle_msg)

    existing = db.query(BusinessProcessDependency).filter(
        BusinessProcessDependency.primary_process_id == process_id,
        BusinessProcessDependency.depends_on_process_id == data.depends_on_process_id,
        BusinessProcessDependency.tenant_id == current_user.tenant_id,
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Dependency already exists")

    dependency = BusinessProcessDependency(
        tenant_id=current_user.tenant_id,
        primary_process_id=process_id,
        depends_on_process_id=data.depends_on_process_id,
        dependency_type=data.dependency_type.value if hasattr(data.dependency_type, 'value') else data.dependency_type,
        description=data.description,
    )
    db.add(dependency)
    db.flush()

    audit_log(
        db=db,
        tenant_id=str(current_user.tenant_id),
        actor_user_id=str(current_user.global_user_id),
        action="create",
        entity_type="business_process_dependency",
        entity_id=str(dependency.id),
        after_json={
            "primary_process_id": str(process_id),
            "depends_on_process_id": str(data.depends_on_process_id),
            "dependency_type": data.dependency_type,
        },
    )

    return BusinessProcessDependencyResponse(
        id=dependency.id,
        tenant_id=dependency.tenant_id,
        primary_process_id=dependency.primary_process_id,
        depends_on_process_id=dependency.depends_on_process_id,
        dependency_type=dependency.dependency_type,
        description=dependency.description,
        created_at=dependency.created_at,
    )


@router.delete("/{process_id}/dependencies/{dependency_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_business_process_dependency(
    db: DB,
    current_user: LocalUser = CurrentUserV2,
    process_id: UUID = None,
    dependency_id: UUID = None,
):
    """Delete a business process dependency."""
    if process_id is None or dependency_id is None:
        raise HTTPException(status_code=400, detail="process_id and dependency_id are required")

    bp = db.query(BusinessProcess).filter(
        BusinessProcess.id == process_id,
        BusinessProcess.tenant_id == current_user.tenant_id,
    ).first()
    if not bp:
        raise HTTPException(status_code=404, detail="Business process not found")

    dependency = db.query(BusinessProcessDependency).filter(
        BusinessProcessDependency.id == dependency_id,
        BusinessProcessDependency.primary_process_id == process_id,
        BusinessProcessDependency.tenant_id == current_user.tenant_id,
    ).first()

    if not dependency:
        raise HTTPException(status_code=404, detail="Dependency not found")

    audit_log(
        db=db,
        tenant_id=str(current_user.tenant_id),
        actor_user_id=str(current_user.global_user_id),
        action="delete",
        entity_type="business_process_dependency",
        entity_id=str(dependency_id),
        before_json={"primary_process_id": str(process_id)},
    )

    db.delete(dependency)
    db.commit()


@router.post("/{process_id}/assets", status_code=status.HTTP_201_CREATED)
def add_process_asset_v2(
    db: DB,
    current_user: LocalUser = CurrentUserV2,
    process_id: UUID = None,
    data: ProcessAssetLinkCreate = None,
):
    """Link an asset to a business process."""
    if process_id is None:
        raise HTTPException(status_code=400, detail="process_id is required")
    if data is None:
        raise HTTPException(status_code=400, detail="Request body required")
    
    bp = db.query(BusinessProcess).filter(
        BusinessProcess.id == process_id,
        BusinessProcess.tenant_id == current_user.tenant_id,
    ).first()

    if not bp:
        raise HTTPException(status_code=404, detail="Business process not found")

    asset = db.query(Asset).filter(
        Asset.id == data.asset_id,
        Asset.tenant_id == current_user.tenant_id,
    ).first()

    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    existing = db.query(ProcessAsset).filter(
        ProcessAsset.business_process_id == process_id,
        ProcessAsset.asset_id == data.asset_id,
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail="Asset already linked")

    link = ProcessAsset(
        tenant_id=current_user.tenant_id,
        business_process_id=process_id,
        asset_id=data.asset_id,
        relation_description=data.relation_description,
    )
    db.add(link)
    db.commit()

    audit_log(
        db=db,
        tenant_id=str(current_user.tenant_id),
        actor_user_id=str(current_user.global_user_id),
        action="link_asset",
        entity_type="business_process",
        entity_id=str(process_id),
        after_json={"asset_id": str(data.asset_id)},
    )

    return {"message": "Asset linked successfully"}


@router.delete("/{process_id}/assets/{asset_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_process_asset_v2(
    db: DB,
    current_user: LocalUser = CurrentUserV2,
    process_id: UUID = None,
    asset_id: UUID = None,
):
    """Unlink an asset from a business process."""
    if process_id is None or asset_id is None:
        raise HTTPException(status_code=400, detail="process_id and asset_id are required")
    
    bp = db.query(BusinessProcess).filter(
        BusinessProcess.id == process_id,
        BusinessProcess.tenant_id == current_user.tenant_id,
    ).first()

    if not bp:
        raise HTTPException(status_code=404, detail="Business process not found")

    link = db.query(ProcessAsset).filter(
        ProcessAsset.business_process_id == process_id,
        ProcessAsset.asset_id == asset_id,
    ).first()

    if not link:
        raise HTTPException(status_code=404, detail="Asset link not found")

    db.delete(link)
    db.commit()

    audit_log(
        db=db,
        tenant_id=str(current_user.tenant_id),
        actor_user_id=str(current_user.global_user_id),
        action="unlink_asset",
        entity_type="business_process",
        entity_id=str(process_id),
        after_json={"asset_id": str(asset_id)},
    )


def _build_response(db: Session, bp: BusinessProcess) -> BusinessProcessResponse:
    """Build a BusinessProcessResponse from a model instance."""
    owner = None
    if bp.owner_user_id:
        user = db.query(User).filter(User.id == bp.owner_user_id).first()
        if user:
            owner = {"id": str(user.id), "name": getattr(user, 'name', '') or getattr(user, 'full_name', ''), "email": getattr(user, 'email', '') or ''}
        else:
            local_user = db.query(LocalUser).filter(LocalUser.id == bp.owner_user_id).first()
            if local_user:
                owner = {"id": str(local_user.id), "name": local_user.full_name, "email": ""}

    asset_links = db.query(ProcessAsset).filter(
        ProcessAsset.business_process_id == bp.id
    ).all()

    process_asset_links = []
    for link in asset_links:
        asset = db.query(Asset).filter(Asset.id == link.asset_id).first()
        asset_summary = None
        if asset:
            asset_summary = {
                "id": asset.id,
                "name": asset.name,
                "asset_type": asset.asset_type,
                "criticality": asset.criticality,
            }
        process_asset_links.append({
            "id": link.id,
            "asset_id": link.asset_id,
            "asset": asset_summary,
            "relation_description": link.relation_description,
        })

    return BusinessProcessResponse(
        id=bp.id,
        tenant_id=bp.tenant_id,
        owner_user_id=bp.owner_user_id,
        division_id=bp.division_id,
        name=bp.name,
        description=bp.description,
        purpose=bp.purpose,
        inputs=bp.inputs,
        outputs=bp.outputs,
        status=bp.status,
        confidentiality_need=bp.confidentiality_need,
        integrity_need=bp.integrity_need,
        availability_need=bp.availability_need,
        owner=owner,
        assets=process_asset_links,
        asset_count=len(process_asset_links),
        created_at=bp.created_at,
        updated_at=bp.updated_at,
    )