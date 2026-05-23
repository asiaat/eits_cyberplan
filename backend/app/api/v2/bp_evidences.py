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
from app.models.imr_item import ImrItem
from app.models.eits_catalog_measure import EitsCatalogMeasure
from app.core.audit import log_audit as audit_log
from app.services.evidence_service import get_evidence_service

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


class LinkedBPInfo(BaseModel):
    """Schema for linked business process info."""
    process_id: UUID
    process_name: str
    link_id: UUID


class LinkedImrItemInfo(BaseModel):
    """Schema for linked IMR item info."""
    imr_item_id: UUID
    measure_code: str
    measure_name: str
    link_id: UUID


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
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
    download_count: int = 0
    download_url: Optional[str] = None
    link_id: UUID
    linked_business_processes: list[LinkedBPInfo] = []
    linked_imr_items: list[LinkedImrItemInfo] = []

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
                file_size=evidence.file_size,
                mime_type=evidence.mime_type,
                download_count=evidence.download_count or 0,
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

    service = get_evidence_service()

    result = []
    for evidence in evidences:
        from app.models.local_user import LocalUser as LU
        owner_name = None
        if evidence.owner_user_id:
            owner = db.query(LU).filter(LU.id == evidence.owner_user_id).first()
            if owner:
                owner_name = owner.full_name

        bp_links = db.query(EvidenceLink).filter(
            EvidenceLink.evidence_id == evidence.id,
            EvidenceLink.target_type == "business_process",
        ).all()

        linked_bps = []
        for bp_link in bp_links:
            bp = db.query(BusinessProcess).filter(BusinessProcess.id == bp_link.target_id).first()
            if bp:
                linked_bps.append(LinkedBPInfo(
                    process_id=bp.id,
                    process_name=bp.name,
                    link_id=bp_link.id,
                ))

        imr_links = db.query(EvidenceLink).filter(
            EvidenceLink.evidence_id == evidence.id,
            EvidenceLink.target_type == "imr_item",
        ).all()

        linked_imr_items = []
        for imr_link in imr_links:
            imr_item = db.query(ImrItem).filter(ImrItem.id == imr_link.target_id).first()
            if imr_item:
                measure = db.query(EitsCatalogMeasure).filter(EitsCatalogMeasure.id == imr_item.measure_id).first()
                measure_code = measure.code if measure else ""
                measure_name = measure.name if measure else ""
                linked_imr_items.append(LinkedImrItemInfo(
                    imr_item_id=imr_item.id,
                    measure_code=measure_code,
                    measure_name=measure_name,
                    link_id=imr_link.id,
                ))

        download_url = service.get_presigned_url(evidence.storage_uri) if evidence.storage_uri else None

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
            file_size=evidence.file_size,
            mime_type=evidence.mime_type,
            download_count=evidence.download_count or 0,
            download_url=download_url,
            link_id=evidence.id,
            linked_business_processes=linked_bps,
            linked_imr_items=linked_imr_items,
        ))

    return result