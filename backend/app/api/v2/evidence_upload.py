"""Evidence Upload API v2."""
from typing import Optional
from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from fastapi.responses import StreamingResponse
from io import BytesIO
from pydantic import BaseModel

from app.api.deps import DB
from app.api.v2.auth import get_current_user_v2, LocalUser
from app.models.evidence import Evidence
from app.services.evidence_service import get_evidence_service, EvidenceService
from app.core.audit import log_audit as audit_log

router = APIRouter()


class EvidenceUploadResponse(BaseModel):
    id: str
    title: str
    evidence_type: str
    file_hash: str
    storage_uri: str
    is_new: bool
    existing_id: Optional[str] = None
    version: str

    model_config = {"from_attributes": True}


class EvidenceResponse(BaseModel):
    id: str
    tenant_id: str
    title: str
    evidence_type: str
    storage_uri: Optional[str] = None
    external_url: Optional[str] = None
    file_hash: Optional[str] = None
    version: Optional[str] = None
    owner_user_id: Optional[str] = None
    owner_name: Optional[str] = None
    valid_from: Optional[str] = None
    valid_until: Optional[str] = None
    review_due_date: Optional[str] = None
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
    download_count: int = 0
    created_at: str
    download_url: Optional[str] = None

    model_config = {"from_attributes": True}


ALLOWED_FILE_TYPES = {
    "application/pdf": ".pdf",
    "application/msword": ".doc",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
    "application/vnd.ms-excel": ".xls",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": ".xlsx",
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "text/plain": ".txt",
}

MAX_FILE_SIZE = 50 * 1024 * 1024


@router.post("/evidences/upload", response_model=EvidenceUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_evidence(
    db: DB,
    current_user: LocalUser = Depends(get_current_user_v2),
    file: UploadFile = File(...),
    title: str = Form(...),
    evidence_type: str = Form("document"),
):
    """Upload evidence file to MinIO storage.

    If the same file (by SHA-256 hash) already exists for this tenant,
    returns the existing evidence record instead of creating a duplicate.

    Supported file types: PDF, DOC, DOCX, XLS, XLSX, JPG, PNG, TXT
    Max file size: 50MB
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is required")

    content = await file.read()

    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size is {MAX_FILE_SIZE // (1024*1024)}MB"
        )

    content_type = file.content_type or "application/octet-stream"

    allowed_ext = ALLOWED_FILE_TYPES.get(content_type)
    if not allowed_ext:
        allowed_types = ", ".join(ALLOWED_FILE_TYPES.keys())
        raise HTTPException(
            status_code=400,
            detail=f"File type not allowed. Allowed types: {allowed_types}"
        )

    try:
        service = get_evidence_service()
        evidence, is_new = service.upload_file(
            db=db,
            file_content=content,
            filename=file.filename,
            content_type=content_type,
            title=title,
            evidence_type=evidence_type,
            tenant_id=current_user.tenant_id,
            owner_user_id=current_user.global_user_id,
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

    audit_log(
        db=db,
        tenant_id=str(current_user.tenant_id),
        actor_user_id=str(current_user.global_user_id),
        action="upload" if is_new else "link_existing",
        entity_type="evidence",
        entity_id=str(evidence.id),
        after_json={
            "title": evidence.title,
            "evidence_type": evidence.evidence_type,
            "is_new": is_new,
        },
    )

    return EvidenceUploadResponse(
        id=str(evidence.id),
        title=evidence.title,
        evidence_type=evidence.evidence_type,
        file_hash=evidence.file_hash or "",
        storage_uri=evidence.storage_uri or "",
        is_new=is_new,
        existing_id=None if is_new else str(evidence.id),
        version=evidence.version or "1.0",
    )


@router.get("/evidences/{evidence_id}", response_model=EvidenceResponse)
def get_evidence(
    db: DB,
    current_user: LocalUser = Depends(get_current_user_v2),
    evidence_id: UUID = None,
):
    """Get evidence details with download URL."""
    evidence = db.query(Evidence).filter(
        Evidence.id == evidence_id,
        Evidence.tenant_id == current_user.tenant_id,
        Evidence.deleted_at.is_(None),
    ).first()

    if not evidence:
        raise HTTPException(status_code=404, detail="Evidence not found")

    download_url = None
    if evidence.storage_uri:
        try:
            service = get_evidence_service()
            download_url = service.get_presigned_url(evidence.storage_uri)
        except Exception:
            pass

    owner_name = None
    if evidence.owner_user_id:
        from app.models.local_user import LocalUser as LU
        owner = db.query(LU).filter(LU.id == evidence.owner_user_id).first()
        if owner:
            owner_name = owner.full_name

    return EvidenceResponse(
        id=str(evidence.id),
        tenant_id=str(evidence.tenant_id),
        title=evidence.title,
        evidence_type=evidence.evidence_type,
        storage_uri=evidence.storage_uri,
        external_url=evidence.external_url,
        file_hash=evidence.file_hash,
        version=evidence.version,
        owner_user_id=str(evidence.owner_user_id) if evidence.owner_user_id else None,
        owner_name=owner_name,
        valid_from=str(evidence.valid_from) if evidence.valid_from else None,
        valid_until=str(evidence.valid_until) if evidence.valid_until else None,
        review_due_date=str(evidence.review_due_date) if evidence.review_due_date else None,
        file_size=evidence.file_size,
        mime_type=evidence.mime_type,
        download_count=evidence.download_count or 0,
        created_at=str(evidence.created_at),
        download_url=download_url,
    )


@router.get("/evidences/{evidence_id}/download")
def download_evidence_file(
    db: DB,
    current_user: LocalUser = Depends(get_current_user_v2),
    evidence_id: UUID = None,
):
    """Download evidence file with proper Content-Disposition header."""
    evidence = db.query(Evidence).filter(
        Evidence.id == evidence_id,
        Evidence.tenant_id == current_user.tenant_id,
    ).first()

    if not evidence:
        raise HTTPException(status_code=404, detail="Evidence not found")

    if not evidence.storage_uri:
        raise HTTPException(status_code=400, detail="No file associated with this evidence")

    evidence.download_count = (evidence.download_count or 0) + 1
    db.commit()

    service = get_evidence_service()
    file_content, content_type = service.get_file(evidence.storage_uri)

    filename = evidence.storage_uri.split("/")[-1]

    return StreamingResponse(
        BytesIO(file_content),
        media_type=content_type or "application/octet-stream",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )


@router.delete("/evidences/{evidence_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_evidence(
    db: DB,
    current_user: LocalUser = Depends(get_current_user_v2),
    evidence_id: UUID = None,
):
    """Delete evidence and its file from storage."""
    evidence = db.query(Evidence).filter(
        Evidence.id == evidence_id,
        Evidence.tenant_id == current_user.tenant_id,
    ).first()

    if not evidence:
        raise HTTPException(status_code=404, detail="Evidence not found")

    evidence.soft_delete(current_user.global_user_id)

    audit_log(
        db=db,
        tenant_id=str(current_user.tenant_id),
        actor_user_id=str(current_user.global_user_id),
        action="delete",
        entity_type="evidence",
        entity_id=str(evidence_id),
        before_json={"title": evidence.title},
    )

    db.commit()


@router.patch("/evidences/{evidence_id}", response_model=EvidenceResponse)
def update_evidence_metadata(
    db: DB,
    current_user: LocalUser = Depends(get_current_user_v2),
    evidence_id: UUID = None,
    title: str = None,
    evidence_type: str = None,
    valid_from: datetime = None,
    valid_until: datetime = None,
    review_due_date: datetime = None,
):
    """Update evidence metadata (not the file)."""
    evidence = db.query(Evidence).filter(
        Evidence.id == evidence_id,
        Evidence.tenant_id == current_user.tenant_id,
    ).first()

    if not evidence:
        raise HTTPException(status_code=404, detail="Evidence not found")

    if title:
        evidence.title = title
    if evidence_type:
        evidence.evidence_type = evidence_type
    if valid_from:
        evidence.valid_from = valid_from
    if valid_until:
        evidence.valid_until = valid_until
    if review_due_date:
        evidence.review_due_date = review_due_date

    db.commit()
    db.refresh(evidence)

    return get_evidence(db, current_user, evidence_id)