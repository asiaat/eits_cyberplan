"""Evidence API endpoints."""
from fastapi import APIRouter, Depends

router = APIRouter()


@router.get("/")
def list_evidences():
    """List evidence."""
    return []


@router.post("/")
def create_evidence():
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