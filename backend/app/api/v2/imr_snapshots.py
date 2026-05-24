from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.api.deps import DB
from app.api.v2.auth import get_current_user_v2, LocalUser
from app.models.imr_snapshot import ImrSnapshot
from app.models.imr_item import ImrItem
from app.models.protectionmode_selection import ProtectionModeSelection
from app.schemas.imr_snapshot import ImrSnapshotResponse, ImrSnapshotCreate, ImrSnapshotList
from app.services.v2.imr_regeneration_service import ImrRegenerationService

router = APIRouter()


def _build_snapshot_response(snapshot: ImrSnapshot, db: Session) -> ImrSnapshotResponse:
    pm_approach = None
    if snapshot.protection_mode_selection_id:
        pm = db.query(ProtectionModeSelection).filter(
            ProtectionModeSelection.id == snapshot.protection_mode_selection_id
        ).first()
        if pm:
            pm_approach = pm.security_approach

    created_by_name = None
    if snapshot.created_by:
        from app.models.local_user import LocalUser
        user = db.query(LocalUser).filter(LocalUser.id == snapshot.created_by).first()
        if user:
            created_by_name = user.full_name

    return ImrSnapshotResponse(
        id=snapshot.id,
        tenant_id=snapshot.tenant_id,
        protection_mode_selection_id=snapshot.protection_mode_selection_id,
        label=snapshot.label,
        description=snapshot.description,
        is_current=snapshot.is_current,
        item_count=snapshot.item_count,
        created_by=snapshot.created_by,
        created_at=snapshot.created_at,
        restored_from=snapshot.restored_from,
        created_by_name=created_by_name,
        pm_approach=pm_approach,
    )


@router.get("/", response_model=ImrSnapshotList)
def list_snapshots(
    db: DB,
    current_user: LocalUser = Depends(get_current_user_v2),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    """List all IMR snapshots for the current tenant."""
    query = db.query(ImrSnapshot).filter(
        ImrSnapshot.tenant_id == current_user.tenant_id,
    ).order_by(ImrSnapshot.created_at.desc())

    total = query.count()
    snapshots = query.offset(offset).limit(limit).all()

    return ImrSnapshotList(
        snapshots=[_build_snapshot_response(s, db) for s in snapshots],
        total_count=total,
    )


@router.get("/{snapshot_id}", response_model=ImrSnapshotResponse)
def get_snapshot(
    db: DB,
    current_user: LocalUser = Depends(get_current_user_v2),
    snapshot_id: UUID = None,
):
    """Get a specific snapshot."""
    snapshot = db.query(ImrSnapshot).filter(
        ImrSnapshot.id == snapshot_id,
        ImrSnapshot.tenant_id == current_user.tenant_id,
    ).first()

    if not snapshot:
        raise HTTPException(status_code=404, detail="Snapshot not found")

    return _build_snapshot_response(snapshot, db)


@router.post("/", response_model=ImrSnapshotResponse, status_code=status.HTTP_201_CREATED)
def create_snapshot(
    db: DB,
    current_user: LocalUser = Depends(get_current_user_v2),
    data: ImrSnapshotCreate = None,
):
    """Manually create a snapshot of current IMR items (snapshot_id IS NULL)."""
    current_items = db.query(ImrItem).filter(
        ImrItem.tenant_id == current_user.tenant_id,
        ImrItem.imr_snapshot_id.is_(None),
    ).all()

    if not current_items:
        raise HTTPException(status_code=400, detail="No current IMR items to snapshot")

    snapshot = ImrSnapshot(
        tenant_id=current_user.tenant_id,
        protection_mode_selection_id=data.protection_mode_selection_id,
        label=data.label,
        description=data.description,
        is_current=False,
        item_count=len(current_items),
        created_by=current_user.id,
    )
    db.add(snapshot)
    db.flush()

    for item in current_items:
        item.imr_snapshot_id = snapshot.id

    db.commit()
    db.refresh(snapshot)

    return _build_snapshot_response(snapshot, db)


@router.post("/{snapshot_id}/restore")
def restore_snapshot(
    db: DB,
    current_user: LocalUser = Depends(get_current_user_v2),
    snapshot_id: UUID = None,
):
    """Restore a snapshot: replace current IMR items with snapshot items."""
    try:
        removed_count = ImrRegenerationService.restore_snapshot(
            db=db,
            tenant_id=current_user.tenant_id,
            snapshot_id=snapshot_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    return {
        "snapshot_id": str(snapshot_id),
        "removed_current_items": removed_count,
        "message": "Snapshot restored successfully",
    }


@router.delete("/{snapshot_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_snapshot(
    db: DB,
    current_user: LocalUser = Depends(get_current_user_v2),
    snapshot_id: UUID = None,
):
    """Delete a snapshot and its associated IMR items."""
    snapshot = db.query(ImrSnapshot).filter(
        ImrSnapshot.id == snapshot_id,
        ImrSnapshot.tenant_id == current_user.tenant_id,
    ).first()

    if not snapshot:
        raise HTTPException(status_code=404, detail="Snapshot not found")

    db.query(ImrItem).filter(
        ImrItem.imr_snapshot_id == snapshot_id,
    ).delete(synchronize_session=False)

    db.delete(snapshot)
    db.commit()
