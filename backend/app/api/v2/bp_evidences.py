"""Business Process Evidence Linking API v2."""
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.api.deps import DB
from app.api.v2.auth import get_current_user_v2, LocalUser
from app.models.evidence import Evidence
from app.models.evidence_link import EvidenceLink
from app.models.business_process import BusinessProcess
from app.core.audit import log_audit as audit_log

router = APIRouter()


class EvidenceLinkCreate(BaseModel):
    """Schema for linking evidence to a business process."""
    evidence_id: UUID


class EvidenceLinkResponse(BaseModel):
    """Schema for evidence link response."""
    id: UUID
    evidence_id: UUID
    target_type: str
    target_id: UUID
    title: Optional[str] = None
    evidence_type: Optional[str] = None
    external_url: Optional[str] = None
    owner_name: Optional[str] = None

    model_config = {"from_attributes": True}


class EvidenceListItem(BaseModel):
    """Schema for evidence item in BP context."""
    id: UUID
    title: str
    evidence_type: str
    external_url: Optional[str] = None
    version: Optional[str] = None
    owner_name: Optional[str] = None
    valid_from: Optional[str] = None
    valid_until: Optional[str] = None
    review_due_date: Optional[str] = None
    link_id: UUID

    model_config = {"from_attributes": True}


@router.get("/business-processes/{process_id}/evidences", response_model=list[EvidenceListItem])
def get_bp_evidences(
    db: DB,
    current_user: LocalUser = Depends(get_current_user_v2),
    process_id: UUID = None,
):
    """Get all evidence items linked to a business process."""
    if process_id is None:
        raise HTTPException(status_code=400, detail="process_id is required")

    bp = db.query(BusinessProcess).filter(
        BusinessProcess.id == process_id,
        BusinessProcess.tenant_id == current_user.tenant_id,
    ).first()

    if not bp:
        raise HTTPException(status_code=404, detail="Business process not found")

    links = db.query(EvidenceLink).filter(
        EvidenceLink.tenant_id == current_user.tenant_id,
        EvidenceLink.target_type == "business_process",
        EvidenceLink.target_id == process_id,
    ).all()

    result = []
    for link in links:
        evidence = db.query(Evidence).filter(Evidence.id == link.evidence_id).first()
        if evidence:
            owner_name = None
            if evidence.owner_user_id:
                from app.models.local_user import LocalUser as LU
                owner = db.query(LU).filter(LU.id == evidence.owner_user_id).first()
                if owner:
                    owner_name = owner.full_name

            result.append(EvidenceListItem(
                id=evidence.id,
                title=evidence.title,
                evidence_type=evidence.evidence_type,
                external_url=evidence.external_url,
                version=evidence.version,
                owner_name=owner_name,
                valid_from=str(evidence.valid_from) if evidence.valid_from else None,
                valid_until=str(evidence.valid_until) if evidence.valid_until else None,
                review_due_date=str(evidence.review_due_date) if evidence.review_due_date else None,
                link_id=link.id,
            ))

    return result


@router.post("/business-processes/{process_id}/evidence-links", status_code=status.HTTP_201_CREATED)
def link_evidence_to_bp(
    db: DB,
    current_user: LocalUser = Depends(get_current_user_v2),
    process_id: UUID = None,
    data: EvidenceLinkCreate = None,
):
    """Link an evidence item to a business process."""
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

    evidence = db.query(Evidence).filter(
        Evidence.id == data.evidence_id,
        Evidence.tenant_id == current_user.tenant_id,
    ).first()

    if not evidence:
        raise HTTPException(status_code=404, detail="Evidence not found")

    existing = db.query(EvidenceLink).filter(
        EvidenceLink.tenant_id == current_user.tenant_id,
        EvidenceLink.evidence_id == data.evidence_id,
        EvidenceLink.target_type == "business_process",
        EvidenceLink.target_id == process_id,
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail="Evidence already linked to this business process")

    link = EvidenceLink(
        tenant_id=current_user.tenant_id,
        evidence_id=data.evidence_id,
        target_type="business_process",
        target_id=process_id,
    )
    db.add(link)
    db.flush()

    audit_log(
        db=db,
        tenant_id=str(current_user.tenant_id),
        actor_user_id=str(current_user.global_user_id),
        action="link",
        entity_type="evidence_link",
        entity_id=str(link.id),
        after_json={
            "evidence_id": str(data.evidence_id),
            "target_type": "business_process",
            "target_id": str(process_id),
        },
    )

    return {"message": "Evidence linked successfully", "link_id": str(link.id)}


@router.delete("/business-processes/{process_id}/evidence-links/{link_id}", status_code=status.HTTP_204_NO_CONTENT)
def unlink_evidence_from_bp(
    db: DB,
    current_user: LocalUser = Depends(get_current_user_v2),
    process_id: UUID = None,
    link_id: UUID = None,
):
    """Unlink an evidence item from a business process."""
    if process_id is None or link_id is None:
        raise HTTPException(status_code=400, detail="process_id and link_id are required")

    bp = db.query(BusinessProcess).filter(
        BusinessProcess.id == process_id,
        BusinessProcess.tenant_id == current_user.tenant_id,
    ).first()

    if not bp:
        raise HTTPException(status_code=404, detail="Business process not found")

    link = db.query(EvidenceLink).filter(
        EvidenceLink.id == link_id,
        EvidenceLink.tenant_id == current_user.tenant_id,
        EvidenceLink.target_type == "business_process",
        EvidenceLink.target_id == process_id,
    ).first()

    if not link:
        raise HTTPException(status_code=404, detail="Evidence link not found")

    audit_log(
        db=db,
        tenant_id=str(current_user.tenant_id),
        actor_user_id=str(current_user.global_user_id),
        action="unlink",
        entity_type="evidence_link",
        entity_id=str(link_id),
        before_json={
            "evidence_id": str(link.evidence_id),
            "target_type": "business_process",
            "target_id": str(process_id),
        },
    )

    db.delete(link)
    db.commit()


@router.get("/evidences", response_model=list[EvidenceListItem])
def list_evidences(
    db: DB,
    current_user: LocalUser = Depends(get_current_user_v2),
    evidence_type: Optional[str] = None,
    search: Optional[str] = None,
):
    """List all evidences for the current tenant (for linking UI)."""
    query = db.query(Evidence).filter(Evidence.tenant_id == current_user.tenant_id)

    if evidence_type:
        query = query.filter(Evidence.evidence_type == evidence_type)

    if search:
        query = query.filter(Evidence.title.ilike(f"%{search}%"))

    evidences = query.order_by(Evidence.created_at.desc()).limit(100).all()

    result = []
    for evidence in evidences:
        from app.models.local_user import LocalUser as LU
        owner_name = None
        if evidence.owner_user_id:
            owner = db.query(LU).filter(LU.id == evidence.owner_user_id).first()
            if owner:
                owner_name = owner.full_name

        result.append(EvidenceListItem(
            id=evidence.id,
            title=evidence.title,
            evidence_type=evidence.evidence_type,
            external_url=evidence.external_url,
            version=evidence.version,
            owner_name=owner_name,
            valid_from=str(evidence.valid_from) if evidence.valid_from else None,
            valid_until=str(evidence.valid_until) if evidence.valid_until else None,
            review_due_date=str(evidence.review_due_date) if evidence.review_due_date else None,
            link_id=evidence.id,
        ))

    return result