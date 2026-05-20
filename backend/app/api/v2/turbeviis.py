"""Turbeviis (Mode of Protection) API v2."""
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import DB
from app.api.v2.auth import get_current_user_v2, LocalUser
from app.models.turbeviis_selection import TurbeviisSelection
from app.models.evidence import Evidence
from app.models.eits_catalog_version import EitsCatalogVersion
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


class TurbeviisSelectionResponse(BaseModel):
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


class TurbeviisSelectionCreate(BaseModel):
    catalog_version_id: Optional[UUID] = None
    security_approach: SecurityApproach = SecurityApproach.BASIC
    notes: Optional[str] = None


class TurbeviisSelectionUpdate(BaseModel):
    security_approach: Optional[SecurityApproach] = None
    evidence_id: Optional[UUID] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None


class EvidenceLinkRequest(BaseModel):
    evidence_id: UUID


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


@router.get("/", response_model=List[TurbeviisSelectionResponse])
def list_turbeviis_selections(
    db: DB,
    current_user: LocalUser = Depends(get_current_user_v2),
    catalog_version_id: Optional[UUID] = None,
):
    """List all turbeviis selections for the current tenant."""
    query = db.query(TurbeviisSelection).filter(
        TurbeviisSelection.tenant_id == current_user.tenant_id
    )

    if catalog_version_id:
        query = query.filter(TurbeviisSelection.catalog_version_id == catalog_version_id)

    selections = query.order_by(TurbeviisSelection.created_at.desc()).all()

    result = []
    for sel in selections:
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

        result.append(TurbeviisSelectionResponse(
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
        ))

    return result


@router.post("/", response_model=TurbeviisSelectionResponse, status_code=status.HTTP_201_CREATED)
def create_turbeviis_selection(
    db: DB,
    current_user: LocalUser = Depends(get_current_user_v2),
    data: TurbeviisSelectionCreate = None,
):
    """Create a new turbeviis selection. Deactivates other selections for the same catalog version."""
    if data and data.catalog_version_id:
        existing = db.query(TurbeviisSelection).filter(
            TurbeviisSelection.tenant_id == current_user.tenant_id,
            TurbeviisSelection.catalog_version_id == data.catalog_version_id,
            TurbeviisSelection.is_active == True,
        ).first()
        if existing:
            existing.is_active = False
            db.commit()

    new_sel = TurbeviisSelection(
        tenant_id=current_user.tenant_id,
        catalog_version_id=data.catalog_version_id if data else None,
        security_approach=data.security_approach.value if data else SecurityApproach.BASIC.value,
        notes=data.notes if data else None,
        is_active=True,
    )
    db.add(new_sel)
    db.commit()
    db.refresh(new_sel)

    catalog_name = None
    if new_sel.catalog_version_id:
        cv = db.query(EitsCatalogVersion).filter(EitsCatalogVersion.id == new_sel.catalog_version_id).first()
        if cv:
            catalog_name = cv.name

    return TurbeviisSelectionResponse(
        id=new_sel.id,
        tenant_id=new_sel.tenant_id,
        catalog_version_id=new_sel.catalog_version_id,
        catalog_version_name=catalog_name,
        security_approach=new_sel.security_approach,
        approach_display=new_sel.security_approach,
        evidence_id=new_sel.evidence_id,
        evidence=None,
        approved_by=new_sel.approved_by,
        approved_by_name=None,
        approved_at=str(new_sel.approved_at) if new_sel.approved_at else None,
        notes=new_sel.notes,
        is_active=new_sel.is_active,
        created_at=str(new_sel.created_at) if new_sel.created_at else None,
        updated_at=str(new_sel.updated_at) if new_sel.updated_at else None,
    )


@router.get("/{selection_id}", response_model=TurbeviisSelectionResponse)
def get_turbeviis_selection(
    db: DB,
    current_user: LocalUser = Depends(get_current_user_v2),
    selection_id: UUID = None,
):
    """Get a specific turbeviis selection."""
    sel = db.query(TurbeviisSelection).filter(
        TurbeviisSelection.id == selection_id,
        TurbeviisSelection.tenant_id == current_user.tenant_id,
    ).first()

    if not sel:
        raise HTTPException(status_code=404, detail="Turbeviis selection not found")

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

    return TurbeviisSelectionResponse(
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


@router.patch("/{selection_id}", response_model=TurbeviisSelectionResponse)
def update_turbeviis_selection(
    db: DB,
    current_user: LocalUser = Depends(get_current_user_v2),
    selection_id: UUID = None,
    data: TurbeviisSelectionUpdate = None,
):
    """Update a turbeviis selection (e.g., link evidence, change approach)."""
    sel = db.query(TurbeviisSelection).filter(
        TurbeviisSelection.id == selection_id,
        TurbeviisSelection.tenant_id == current_user.tenant_id,
    ).first()

    if not sel:
        raise HTTPException(status_code=404, detail="Turbeviis selection not found")

    if data.security_approach is not None:
        sel.security_approach = data.security_approach.value
    if data.evidence_id is not None:
        sel.evidence_id = data.evidence_id
    if data.notes is not None:
        sel.notes = data.notes
    if data.is_active is not None:
        if data.is_active:
            existing_active = db.query(TurbeviisSelection).filter(
                TurbeviisSelection.tenant_id == current_user.tenant_id,
                TurbeviisSelection.catalog_version_id == sel.catalog_version_id,
                TurbeviisSelection.is_active == True,
                TurbeviisSelection.id != selection_id,
            ).all()
            for ea in existing_active:
                ea.is_active = False
        sel.is_active = data.is_active

    db.commit()
    db.refresh(sel)

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

    return TurbeviisSelectionResponse(
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


@router.delete("/{selection_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_turbeviis_selection(
    db: DB,
    current_user: LocalUser = Depends(get_current_user_v2),
    selection_id: UUID = None,
):
    """Delete a turbeviis selection."""
    sel = db.query(TurbeviisSelection).filter(
        TurbeviisSelection.id == selection_id,
        TurbeviisSelection.tenant_id == current_user.tenant_id,
    ).first()

    if not sel:
        raise HTTPException(status_code=404, detail="Turbeviis selection not found")

    db.delete(sel)
    db.commit


@router.post("/{selection_id}/link-evidence", response_model=TurbeviisSelectionResponse)
def link_evidence_to_turbeviis(
    db: DB,
    current_user: LocalUser = Depends(get_current_user_v2),
    selection_id: UUID = None,
    data: EvidenceLinkRequest = None,
):
    """Link an evidence document to a turbeviis selection."""
    sel = db.query(TurbeviisSelection).filter(
        TurbeviisSelection.id == selection_id,
        TurbeviisSelection.tenant_id == current_user.tenant_id,
    ).first()

    if not sel:
        raise HTTPException(status_code=404, detail="Turbeviis selection not found")

    evidence = db.query(Evidence).filter(
        Evidence.id == data.evidence_id,
        Evidence.tenant_id == current_user.tenant_id,
    ).first()

    if not evidence:
        raise HTTPException(status_code=404, detail="Evidence not found")

    sel.evidence_id = data.evidence_id
    db.commit()
    db.refresh(sel)

    catalog_name = None
    if sel.catalog_version_id:
        cv = db.query(EitsCatalogVersion).filter(EitsCatalogVersion.id == sel.catalog_version_id).first()
        if cv:
            catalog_name = cv.name

    evidence_info = LinkedEvidenceInfo(
        id=evidence.id,
        title=evidence.title,
        evidence_type=evidence.evidence_type,
        file_hash=evidence.file_hash,
    )

    return TurbeviisSelectionResponse(
        id=sel.id,
        tenant_id=sel.tenant_id,
        catalog_version_id=sel.catalog_version_id,
        catalog_version_name=catalog_name,
        security_approach=sel.security_approach,
        approach_display=sel.security_approach,
        evidence_id=sel.evidence_id,
        evidence=evidence_info,
        approved_by=sel.approved_by,
        approved_by_name=None,
        approved_at=str(sel.approved_at) if sel.approved_at else None,
        notes=sel.notes,
        is_active=sel.is_active,
        created_at=str(sel.created_at) if sel.created_at else None,
        updated_at=str(sel.updated_at) if sel.updated_at else None,
    )


@router.delete("/{selection_id}/unlink-evidence", response_model=TurbeviisSelectionResponse)
def unlink_evidence_from_turbeviis(
    db: DB,
    current_user: LocalUser = Depends(get_current_user_v2),
    selection_id: UUID = None,
):
    """Unlink evidence from a turbeviis selection."""
    sel = db.query(TurbeviisSelection).filter(
        TurbeviisSelection.id == selection_id,
        TurbeviisSelection.tenant_id == current_user.tenant_id,
    ).first()

    if not sel:
        raise HTTPException(status_code=404, detail="Turbeviis selection not found")

    sel.evidence_id = None
    db.commit()
    db.refresh(sel)

    catalog_name = None
    if sel.catalog_version_id:
        cv = db.query(EitsCatalogVersion).filter(EitsCatalogVersion.id == sel.catalog_version_id).first()
        if cv:
            catalog_name = cv.name

    return TurbeviisSelectionResponse(
        id=sel.id,
        tenant_id=sel.tenant_id,
        catalog_version_id=sel.catalog_version_id,
        catalog_version_name=catalog_name,
        security_approach=sel.security_approach,
        approach_display=sel.security_approach,
        evidence_id=None,
        evidence=None,
        approved_by=sel.approved_by,
        approved_by_name=None,
        approved_at=str(sel.approved_at) if sel.approved_at else None,
        notes=sel.notes,
        is_active=sel.is_active,
        created_at=str(sel.created_at) if sel.created_at else None,
        updated_at=str(sel.updated_at) if sel.updated_at else None,
    )