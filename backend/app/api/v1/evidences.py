"""Evidence API endpoints."""
from fastapi import APIRouter, Depends

from app.api.deps import DB, CurrentUser

router = APIRouter()


@router.get("/")
def list_evidences(db: DB, current_user: CurrentUser):
    """List evidence."""
    from app.models.evidence import Evidence
    return db.query(Evidence).filter(Evidence.tenant_id == current_user.tenant_id).all()


@router.post("/")
def create_evidence(db: DB, current_user: CurrentUser):
    """Create evidence."""
    return {}


@router.get("/{evidence_id}")
def get_evidence(evidence_id: str):
    """Get evidence by ID."""
    return {"id": evidence_id}


@router.patch("/{evidence_id}")
def update_evidence(evidence_id: str):
    """Update evidence."""
    return {"id": evidence_id}


@router.delete("/{evidence_id}")
def delete_evidence(evidence_id: str):
    """Delete evidence."""
    return {"message": "Deleted"}


@router.post("/{evidence_id}/links")
def link_evidence(evidence_id: str):
    """Link evidence to a target."""
    return {}