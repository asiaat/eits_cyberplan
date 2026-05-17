"""Assets API v2."""
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import DB
from app.api.v2.auth import get_current_user_v2, CurrentUserV2, LocalUser
from app.models.asset import Asset
from app.models.process_asset import ProcessAsset
from app.models.business_process import BusinessProcess
from app.models.user import User
from app.models.local_user import EITSRole, UserRole
from app.schemas.asset import (
    AssetCreate,
    AssetUpdate,
    AssetResponse,
    AssetListItem,
    LinkedProcessInfo,
)
from app.core.audit import log_audit as audit_log

router = APIRouter()


def _can_manage_asset_links(db: Session, asset: Asset, current_user: LocalUser) -> bool:
    """Check if user can manage asset-process links (is owner or has infoturbejuht role)."""
    # Asset owner can always manage links
    if asset.owner_user_id == current_user.id:
        return True
    
    # Check if user has infoturbejuht role in EITSRole table (per-tenant roles)
    user_roles = db.query(UserRole).filter(
        UserRole.user_id == current_user.id
    ).all()
    
    if not user_roles:
        return False
        
    role_ids = [str(ur.role_id) for ur in user_roles]
    
    if role_ids:
        infoturbejuht_role = db.query(EITSRole).filter(
            EITSRole.id.in_(role_ids),
            EITSRole.role_name == "Infoturbejuht"  # Case sensitive!
        ).first()
        if infoturbejuht_role:
            return True
    
    # Check if user has any admin-type global role
    from app.models.membership import Membership
    memberships = db.query(Membership).filter(
        Membership.user_id == current_user.id
    ).all()
    
    for mem in memberships:
        if mem.role_id in ['admin', 'administrator', 'superadmin']:
            return True
    
    return False


def _get_linked_processes(db: Session, asset_id: UUID) -> list[LinkedProcessInfo]:
    """Get list of linked business processes for an asset."""
    links = db.query(ProcessAsset).filter(
        ProcessAsset.asset_id == asset_id
    ).all()

    processes = []
    for link in links:
        bp = db.query(BusinessProcess).filter(
            BusinessProcess.id == link.business_process_id
        ).first()
        if bp:
            processes.append(LinkedProcessInfo(
                id=bp.id,
                name=bp.name,
                status=bp.status
            ))
    return processes


def _build_response(db: Session, asset: Asset, current_user: LocalUser = None) -> AssetResponse:
    """Build an AssetResponse from a model instance."""
    owner = None
    if asset.owner_user_id:
        user = db.query(User).filter(User.id == asset.owner_user_id).first()
        if user:
            owner = {"id": str(user.id), "name": getattr(user, 'name', '') or getattr(user, 'full_name', ''), "email": getattr(user, 'email', '') or ''}
        else:
            local_user = db.query(LocalUser).filter(LocalUser.id == asset.owner_user_id).first()
            if local_user:
                owner = {"id": str(local_user.id), "name": local_user.full_name, "email": ""}

    linked_processes = _get_linked_processes(db, asset.id)
    can_manage = _can_manage_asset_links(db, asset, current_user) if current_user else False

    return AssetResponse(
        id=asset.id,
        tenant_id=asset.tenant_id,
        name=asset.name,
        asset_type=asset.asset_type,
        description=asset.description,
        criticality=asset.criticality,
        confidentiality_need=asset.confidentiality_need,
        integrity_need=asset.integrity_need,
        availability_need=asset.availability_need,
        lifecycle_status=asset.lifecycle_status,
        owner_user_id=asset.owner_user_id,
        person_id=asset.person_id,
        owner=owner,
        linked_process_count=len(linked_processes),
        linked_processes=linked_processes,
        can_manage_links=can_manage,
        created_at=asset.created_at,
        updated_at=asset.updated_at,
    )


@router.get("/", response_model=list[AssetListItem])
def list_assets_v2(
    db: DB,
    current_user: LocalUser = CurrentUserV2,
    type_filter: Optional[str] = Query(None, alias="type"),
    status_filter: Optional[str] = Query(None, alias="status"),
    owner_id: Optional[UUID] = Query(None, alias="owner_id"),
    person_id: Optional[UUID] = Query(None, alias="person_id"),
    search: Optional[str] = Query(None, description="Search by name"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
):
    """List assets for the current tenant."""
    query = db.query(Asset).filter(
        Asset.tenant_id == current_user.tenant_id
    )

    if type_filter:
        query = query.filter(Asset.asset_type == type_filter)
    if status_filter:
        query = query.filter(Asset.lifecycle_status == status_filter)
    if owner_id:
        query = query.filter(Asset.owner_user_id == owner_id)
    if person_id:
        query = query.filter(Asset.person_id == person_id)
    if search:
        query = query.filter(Asset.name.ilike(f"%{search}%"))

    assets = query.order_by(Asset.created_at.desc()).offset(skip).limit(limit).all()

    result = []
    for asset in assets:
        owner = None
        if asset.owner_user_id:
            user = db.query(User).filter(User.id == asset.owner_user_id).first()
            if user:
                owner = {"id": str(user.id), "name": getattr(user, 'name', '') or getattr(user, 'full_name', ''), "email": getattr(user, 'email', '') or ''}
            else:
                local_user = db.query(LocalUser).filter(LocalUser.id == asset.owner_user_id).first()
                if local_user:
                    owner = {"id": str(local_user.id), "name": local_user.full_name, "email": ""}

        linked_processes = _get_linked_processes(db, asset.id)
        can_manage = _can_manage_asset_links(db, asset, current_user)

        item = AssetListItem(
            id=asset.id,
            tenant_id=asset.tenant_id,
            name=asset.name,
            asset_type=asset.asset_type,
            criticality=asset.criticality,
            confidentiality_need=asset.confidentiality_need,
            integrity_need=asset.integrity_need,
            availability_need=asset.availability_need,
            lifecycle_status=asset.lifecycle_status,
            owner_user_id=asset.owner_user_id,
            person_id=asset.person_id,
            owner=owner,
            linked_process_count=len(linked_processes),
            linked_processes=linked_processes,
            can_manage_links=can_manage,
            created_at=asset.created_at,
        )
        result.append(item)

    return result


@router.post("/", response_model=AssetResponse, status_code=status.HTTP_201_CREATED)
def create_asset_v2(
    db: DB,
    current_user: LocalUser = CurrentUserV2,
    data: AssetCreate = None,
):
    """Create a new asset."""
    if data is None:
        raise HTTPException(status_code=400, detail="Request body required")

    asset = Asset(
        tenant_id=current_user.tenant_id,
        name=data.name,
        asset_type=data.asset_type.value if hasattr(data.asset_type, 'value') else data.asset_type,
        description=data.description,
        criticality=data.criticality.value if hasattr(data.criticality, 'value') else data.criticality,
        confidentiality_need=data.confidentiality_need.value if hasattr(data.confidentiality_need, 'value') else data.confidentiality_need,
        integrity_need=data.integrity_need.value if hasattr(data.integrity_need, 'value') else data.integrity_need,
        availability_need=data.availability_need.value if hasattr(data.availability_need, 'value') else data.availability_need,
        lifecycle_status=data.lifecycle_status.value if hasattr(data.lifecycle_status, 'value') else data.lifecycle_status,
        owner_user_id=data.owner_user_id,
        person_id=data.person_id,
    )
    db.add(asset)
    db.commit()
    db.refresh(asset)

    audit_log(
        db=db,
        tenant_id=str(current_user.tenant_id),
        actor_user_id=str(current_user.global_user_id),
        action="create",
        entity_type="asset",
        entity_id=str(asset.id),
        after_json={"asset": asset.name, "type": asset.asset_type},
    )

    return _build_response(db, asset, current_user)


@router.get("/{asset_id}", response_model=AssetResponse)
def get_asset_v2(
    db: DB,
    current_user: LocalUser = CurrentUserV2,
    asset_id: UUID = None,
):
    """Get an asset by ID."""
    if asset_id is None or (isinstance(asset_id, str) and asset_id == "undefined"):
        raise HTTPException(status_code=400, detail="asset_id is required")

    asset = db.query(Asset).filter(
        Asset.id == asset_id,
        Asset.tenant_id == current_user.tenant_id,
    ).first()

    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    return _build_response(db, asset, current_user)


@router.patch("/{asset_id}/", response_model=AssetResponse)
def update_asset_v2(
    db: DB,
    current_user: LocalUser = CurrentUserV2,
    asset_id: UUID = None,
    data: AssetUpdate = None,
):
    """Update an asset."""
    if asset_id is None:
        raise HTTPException(status_code=400, detail="asset_id is required")
    if data is None:
        raise HTTPException(status_code=400, detail="Request body required")

    asset = db.query(Asset).filter(
        Asset.id == asset_id,
        Asset.tenant_id == current_user.tenant_id,
    ).first()

    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    before = {
        "name": asset.name,
        "asset_type": asset.asset_type,
        "criticality": asset.criticality,
    }

    update_data = data.model_dump(exclude_unset=True, exclude_none=True)
    enum_fields = ("asset_type", "criticality", "confidentiality_need", "integrity_need", "availability_need", "lifecycle_status")

    for field, value in update_data.items():
        if field in enum_fields and hasattr(value, 'value'):
            value = value.value
        if hasattr(asset, field):
            setattr(asset, field, value)

    db.commit()
    db.refresh(asset)

    audit_log(
        db=db,
        tenant_id=str(current_user.tenant_id),
        actor_user_id=str(current_user.global_user_id),
        action="update",
        entity_type="asset",
        entity_id=str(asset.id),
        before_json=before,
        after_json={"asset": asset.name},
    )

    return _build_response(db, asset, current_user)


@router.delete("/{asset_id}/", status_code=status.HTTP_204_NO_CONTENT)
def delete_asset_v2(
    db: DB,
    current_user: LocalUser = CurrentUserV2,
    asset_id: UUID = None,
):
    """Delete an asset if it has no active process links."""
    if asset_id is None:
        raise HTTPException(status_code=400, detail="asset_id is required")

    asset = db.query(Asset).filter(
        Asset.id == asset_id,
        Asset.tenant_id == current_user.tenant_id,
    ).first()

    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    linked_processes = _get_linked_processes(db, asset_id)
    if linked_processes:
        process_names = [p.name for p in linked_processes]
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete: asset is linked to {len(linked_processes)} business process(es): {', '.join(process_names)}. Unlink the asset first."
        )

    db.delete(asset)
    db.commit()

    audit_log(
        db=db,
        tenant_id=str(current_user.tenant_id),
        actor_user_id=str(current_user.global_user_id),
        action="delete",
        entity_type="asset",
        entity_id=str(asset_id),
        before_json={"asset": asset.name, "type": asset.asset_type},
    )


@router.post("/{asset_id}/processes/{process_id}")
def link_asset_to_process(
    db: DB,
    current_user: LocalUser = CurrentUserV2,
    asset_id: UUID = None,
    process_id: UUID = None,
):
    """Link an asset to a business process."""
    if asset_id is None or process_id is None:
        raise HTTPException(status_code=400, detail="asset_id and process_id are required")

    asset = db.query(Asset).filter(
        Asset.id == asset_id,
        Asset.tenant_id == current_user.tenant_id,
    ).first()

    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    if not _can_manage_asset_links(db, asset, current_user):
        raise HTTPException(status_code=403, detail="Not authorized to manage asset links")

    bp = db.query(BusinessProcess).filter(
        BusinessProcess.id == process_id,
        BusinessProcess.tenant_id == current_user.tenant_id,
    ).first()

    if not bp:
        raise HTTPException(status_code=404, detail="Business process not found")

    existing = db.query(ProcessAsset).filter(
        ProcessAsset.business_process_id == process_id,
        ProcessAsset.asset_id == asset_id,
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail="Asset already linked to this process")

    link = ProcessAsset(
        tenant_id=current_user.tenant_id,
        business_process_id=process_id,
        asset_id=asset_id,
    )
    db.add(link)
    db.commit()

    audit_log(
        db=db,
        tenant_id=str(current_user.tenant_id),
        actor_user_id=str(current_user.global_user_id),
        action="link_asset",
        entity_type="asset",
        entity_id=str(asset_id),
        after_json={"process_id": str(process_id), "process_name": bp.name},
    )

    return {"message": "Asset linked to process successfully"}


@router.delete("/{asset_id}/processes/{process_id}", status_code=status.HTTP_204_NO_CONTENT)
def unlink_asset_from_process(
    db: DB,
    current_user: LocalUser = CurrentUserV2,
    asset_id: UUID = None,
    process_id: UUID = None,
):
    """Unlink an asset from a business process."""
    if asset_id is None or process_id is None:
        raise HTTPException(status_code=400, detail="asset_id and process_id are required")

    asset = db.query(Asset).filter(
        Asset.id == asset_id,
        Asset.tenant_id == current_user.tenant_id,
    ).first()

    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    if not _can_manage_asset_links(db, asset, current_user):
        raise HTTPException(status_code=403, detail="Not authorized to manage asset links")

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
        entity_type="asset",
        entity_id=str(asset_id),
        after_json={"process_id": str(process_id)},
    )


@router.get("/{asset_id}/unlinked-processes", response_model=list[dict])
def list_unlinked_processes(
    db: DB,
    current_user: LocalUser = CurrentUserV2,
    asset_id: UUID = None,
):
    """List business processes that are not linked to this asset."""
    if asset_id is None:
        raise HTTPException(status_code=400, detail="asset_id is required")

    asset = db.query(Asset).filter(
        Asset.id == asset_id,
        Asset.tenant_id == current_user.tenant_id,
    ).first()

    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    linked_process_ids = db.query(ProcessAsset.asset_id).filter(
        ProcessAsset.asset_id == asset_id
    ).all()
    linked_ids = [lp[0] for lp in linked_process_ids]

    query = db.query(BusinessProcess).filter(
        BusinessProcess.tenant_id == current_user.tenant_id
    )
    if linked_ids:
        query = query.filter(BusinessProcess.id.notin_(linked_ids))

    processes = query.order_by(BusinessProcess.name).all()

    return [
        {"id": str(p.id), "name": p.name, "status": p.status}
        for p in processes
    ]