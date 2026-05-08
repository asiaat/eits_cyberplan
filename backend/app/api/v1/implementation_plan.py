"""Implementation Plan API endpoints."""
from fastapi import APIRouter, Depends

from app.api.deps import DB, CurrentUser

router = APIRouter()


@router.get("/")
def list_implementation_plan(db: DB, current_user: CurrentUser):
    """List implementation plan items."""
    from app.models.implementation_plan_item import ImplementationPlanItem
    return db.query(ImplementationPlanItem).filter(ImplementationPlanItem.tenant_id == current_user.tenant_id).all()


@router.post("/generate")
def generate_implementation_plan():
    """Generate IMR from selected modules."""
    return []


@router.get("/{item_id}")
def get_implementation_item(item_id: str):
    """Get an IMR item by ID."""
    return {"id": item_id}


@router.patch("/{item_id}")
def update_implementation_item(item_id: str):
    """Update an IMR item."""
    return {"id": item_id}


@router.post("/{item_id}/evidence")
def add_evidence_to_item(item_id: str):
    """Add evidence to an IMR item."""
    return {}


@router.post("/{item_id}/comments")
def add_comment_to_item(item_id: str):
    """Add a comment to an IMR item."""
    return {}


@router.post("/export")
def export_implementation_plan():
    """Export implementation plan."""
    return {}