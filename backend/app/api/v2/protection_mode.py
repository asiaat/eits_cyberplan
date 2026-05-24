"""ProtectionMode (Mode of Protection) API v2."""
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import DB
from app.api.v2.auth import get_current_user_v2, LocalUser
from app.models.protectionmode_selection import ProtectionModeSelection
from app.models.evidence import Evidence
from app.models.eits_catalog_version import EitsCatalogVersion
from app.services.v2.imr_regeneration_service import ImrRegenerationService
from enum import Enum


router = APIRouter()


class SecurityApproach(str, Enum):
    BASIC = "BASIC"
    STANDARD = "STANDARD"
    CORE = "CORE"


class LinkedEvidenceInfo(BaseModel):
    id: UUID
    title: str
    evidence_type: str
    file_hash: Optional[str] = None


class ProtectionModeSelectionResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    catalog_version_id: Optional[UUID] = None
    catalog_version_name: Optional[str] = None
    security_approach: str
    approach_display: str
    evidence_id: Optional[UUID] = None
    evidence: Optional[LinkedEvidenceInfo] = None
    approved_by: Optional[UUID] = None
    approved_by_name: Optional[str] = None
    approved_at: Optional[str] = None
    notes: Optional[str] = None
    is_active: bool
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}


class ProtectionModeSelectionCreate(BaseModel):
    catalog_version_id: Optional[UUID] = None
    security_approach: SecurityApproach = SecurityApproach.BASIC
    notes: Optional[str] = None


class ProtectionModeSelectionUpdate(BaseModel):
    security_approach: Optional[SecurityApproach] = None
    evidence_id: Optional[UUID] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None


class EvidenceLinkRequest(BaseModel):
    evidence_id: UUID


def _build_selection_response(sel: ProtectionModeSelection, db: DB) -> ProtectionModeSelectionResponse:
    """Helper to build selection response from model."""
    catalog_name = None
    if sel.catalog_version_id:
        cv = db.query(EitsCatalogVersion).filter(EitsCatalogVersion.id == sel.catalog_version_id).first()
        if cv:
            catalog_name = cv.name

    evidence_info = None
    if sel.evidence_id:
        ev = db.query(Evidence).filter(Evidence.id == sel.evidence_id).first()
        if ev:
            evidence_info = LinkedEvidenceInfo(
                id=ev.id,
                title=ev.title,
                evidence_type=ev.evidence_type,
                file_hash=ev.file_hash,
            )

    approved_by_name = None
    if sel.approved_by:
        from app.models.local_user import LocalUser as LU
        user = db.query(LU).filter(LU.id == sel.approved_by).first()
        if user:
            approved_by_name = user.full_name

    return ProtectionModeSelectionResponse(
        id=sel.id,
        tenant_id=sel.tenant_id,
        catalog_version_id=sel.catalog_version_id,
        catalog_version_name=catalog_name,
        security_approach=sel.security_approach,
        approach_display=sel.security_approach,
        evidence_id=sel.evidence_id,
        evidence=evidence_info,
        approved_by=sel.approved_by,
        approved_by_name=approved_by_name,
        approved_at=str(sel.approved_at) if sel.approved_at else None,
        notes=sel.notes,
        is_active=sel.is_active,
        created_at=str(sel.created_at) if sel.created_at else None,
        updated_at=str(sel.updated_at) if sel.updated_at else None,
    )


@router.get("/approaches/list")
def list_approaches(
    current_user: LocalUser = Depends(get_current_user_v2),
):
    """Get list of available security approaches (codes only)."""
    return {
        "approaches": [
            {"code": "BASIC"},
            {"code": "STANDARD"},
            {"code": "CORE"},
        ]
    }


@router.get("/", response_model=List[ProtectionModeSelectionResponse])
def list_protectionmode_selections(
    db: DB,
    current_user: LocalUser = Depends(get_current_user_v2),
    catalog_version_id: Optional[UUID] = None,
):
    """List all protection mode selections for the current tenant."""
    query = db.query(ProtectionModeSelection).filter(
        ProtectionModeSelection.tenant_id == current_user.tenant_id,
        ProtectionModeSelection.deleted_at.is_(None),
    )

    if catalog_version_id:
        query = query.filter(ProtectionModeSelection.catalog_version_id == catalog_version_id)

    selections = query.order_by(ProtectionModeSelection.created_at.desc()).all()

    return [_build_selection_response(sel, db) for sel in selections]


@router.post("/", response_model=ProtectionModeSelectionResponse, status_code=status.HTTP_201_CREATED)
def create_or_activate_protectionmode(
    db: DB,
    current_user: LocalUser = Depends(get_current_user_v2),
    data: ProtectionModeSelectionCreate = None,
):
    """Create a new protection mode selection OR activate existing one for this approach.

    If a selection for this security_approach already exists (in any state),
    this will activate it and deactivate all others.
    """
    approach_code = data.security_approach.value if data else SecurityApproach.BASIC.value

    # Check if selection for this approach already exists
    existing = db.query(ProtectionModeSelection).filter(
        ProtectionModeSelection.tenant_id == current_user.tenant_id,
        ProtectionModeSelection.security_approach == approach_code,
    ).first()

    if existing:
        # Deactivate ALL other selections for this tenant
        db.query(ProtectionModeSelection).filter(
            ProtectionModeSelection.tenant_id == current_user.tenant_id,
            ProtectionModeSelection.id != existing.id,
        ).update({"is_active": False})

        # Activate the existing selection
        existing.is_active = True
        db.commit()
        db.refresh(existing)

        return _build_selection_response(existing, db)

    # Deactivate ALL other selections for this tenant (no catalog filter - full deactivation)
    db.query(ProtectionModeSelection).filter(
        ProtectionModeSelection.tenant_id == current_user.tenant_id,
    ).update({"is_active": False})

    # Create new selection
    new_sel = ProtectionModeSelection(
        tenant_id=current_user.tenant_id,
        catalog_version_id=data.catalog_version_id if data else None,
        security_approach=approach_code,
        notes=data.notes if data else None,
        is_active=True,
    )
    db.add(new_sel)
    db.commit()
    db.refresh(new_sel)

    return _build_selection_response(new_sel, db)


@router.get("/{selection_id}", response_model=ProtectionModeSelectionResponse)
def get_protectionmode_selection(
    db: DB,
    current_user: LocalUser = Depends(get_current_user_v2),
    selection_id: UUID = None,
):
    """Get a specific protection mode selection."""
    sel = db.query(ProtectionModeSelection).filter(
        ProtectionModeSelection.id == selection_id,
        ProtectionModeSelection.tenant_id == current_user.tenant_id,
        ProtectionModeSelection.deleted_at.is_(None),
    ).first()

    if not sel:
        raise HTTPException(status_code=404, detail="Protection mode selection not found")

    return _build_selection_response(sel, db)


@router.patch("/{selection_id}", response_model=ProtectionModeSelectionResponse)
def update_protectionmode_selection(
    db: DB,
    current_user: LocalUser = Depends(get_current_user_v2),
    selection_id: UUID = None,
    data: ProtectionModeSelectionUpdate = None,
):
    """Update a protection mode selection (e.g., link evidence, change approach, activate/deactivate)."""
    sel = db.query(ProtectionModeSelection).filter(
        ProtectionModeSelection.id == selection_id,
        ProtectionModeSelection.tenant_id == current_user.tenant_id,
    ).first()

    if not sel:
        raise HTTPException(status_code=404, detail="Protection mode selection not found")

    # If activating this selection, deactivate ALL others first
    if data.is_active is True:
        db.query(ProtectionModeSelection).filter(
            ProtectionModeSelection.tenant_id == current_user.tenant_id,
            ProtectionModeSelection.id != selection_id,
        ).update({"is_active": False})

    if data.security_approach is not None:
        sel.security_approach = data.security_approach.value
    if data.evidence_id is not None:
        sel.evidence_id = data.evidence_id
    if data.notes is not None:
        sel.notes = data.notes
    if data.is_active is not None:
        sel.is_active = data.is_active

    db.commit()
    db.refresh(sel)

    return _build_selection_response(sel, db)


@router.delete("/{selection_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_protectionmode_selection(
    db: DB,
    current_user: LocalUser = Depends(get_current_user_v2),
    selection_id: UUID = None,
):
    """Delete a protection mode selection."""
    sel = db.query(ProtectionModeSelection).filter(
        ProtectionModeSelection.id == selection_id,
        ProtectionModeSelection.tenant_id == current_user.tenant_id,
    ).first()

    if not sel:
        raise HTTPException(status_code=404, detail="Protection mode selection not found")

    sel.soft_delete(current_user.global_user_id)
    db.commit()


@router.post("/{selection_id}/link-evidence", response_model=ProtectionModeSelectionResponse)
def link_evidence_to_protectionmode(
    db: DB,
    current_user: LocalUser = Depends(get_current_user_v2),
    selection_id: UUID = None,
    data: EvidenceLinkRequest = None,
):
    """Link an evidence document to a protection mode selection."""
    sel = db.query(ProtectionModeSelection).filter(
        ProtectionModeSelection.id == selection_id,
        ProtectionModeSelection.tenant_id == current_user.tenant_id,
    ).first()

    if not sel:
        raise HTTPException(status_code=404, detail="Protection mode selection not found")

    evidence = db.query(Evidence).filter(
        Evidence.id == data.evidence_id,
        Evidence.tenant_id == current_user.tenant_id,
    ).first()

    if not evidence:
        raise HTTPException(status_code=404, detail="Evidence not found")

    sel.evidence_id = data.evidence_id
    db.commit()
    db.refresh(sel)

    return _build_selection_response(sel, db)


@router.delete("/{selection_id}/unlink-evidence", response_model=ProtectionModeSelectionResponse)
def unlink_evidence_from_protectionmode(
    db: DB,
    current_user: LocalUser = Depends(get_current_user_v2),
    selection_id: UUID = None,
):
    """Unlink evidence from a protection mode selection."""
    sel = db.query(ProtectionModeSelection).filter(
        ProtectionModeSelection.id == selection_id,
        ProtectionModeSelection.tenant_id == current_user.tenant_id,
    ).first()

    if not sel:
        raise HTTPException(status_code=404, detail="Protection mode selection not found")

    sel.evidence_id = None
    db.commit()
    db.refresh(sel)

    return _build_selection_response(sel, db)


@router.post("/regenerate-imr")
def regenerate_imr_after_mode_change(
    db: DB,
    current_user: LocalUser = Depends(get_current_user_v2),
):
    """Regenerate all IMR items based on active protection mode.

    When protection mode changes, this endpoint clears all existing IMR items
    for the tenant and creates new ones based on the active protection approach.
    PEARO status is set to 'U' (Unknown) for all generated items.
    """
    active = db.query(ProtectionModeSelection).filter(
        ProtectionModeSelection.tenant_id == current_user.tenant_id,
        ProtectionModeSelection.is_active == True,
    ).first()

    if not active:
        raise HTTPException(status_code=400, detail="No active protection mode set")

    result = ImrRegenerationService.regenerate_for_tenant(
        db=db,
        tenant_id=current_user.tenant_id,
        approach=active.security_approach,
    )

    return result


@router.get("/imr-preview")
def get_imr_preview_for_approach(
    db: DB,
    current_user: LocalUser = Depends(get_current_user_v2),
    approach: str = None,
):
    """Get preview of how many IMR items would be generated for a given approach."""
    if approach not in ("BASIC", "STANDARD", "CORE"):
        raise HTTPException(status_code=400, detail="Invalid approach. Use BASIC, STANDARD, or CORE")

    stats = ImrRegenerationService.get_approach_stats(db, approach)
    return stats
