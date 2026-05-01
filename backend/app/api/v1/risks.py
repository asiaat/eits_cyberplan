"""Risks API endpoints."""
from fastapi import APIRouter, Depends

router = APIRouter()


@router.get("/")
def list_risks():
    """List risks."""
    return []


@router.post("/")
def create_risk():
    """Create a risk."""
    return {}


@router.get("/{risk_id}")
def get_risk(risk_id: str):
    """Get a risk by ID."""
    return {"id": risk_id}


@router.patch("/{risk_id}")
def update_risk(risk_id: str):
    """Update a risk."""
    return {"id": risk_id}


@router.delete("/{risk_id}")
def delete_risk(risk_id: str):
    """Delete a risk."""
    return {"message": "Deleted"}


@router.post("/{risk_id}/measures")
def link_measures_to_risk(risk_id: str):
    """Link measures to a risk."""
    return {}


@router.post("/{risk_id}/review")
def review_risk(risk_id: str):
    """Review a risk."""
    return {"id": risk_id}