"""Assets API endpoints."""
from fastapi import APIRouter, Depends

router = APIRouter()


@router.get("/")
def list_assets():
    """List assets."""
    return []


@router.post("/")
def create_asset():
    """Create an asset."""
    return {}


@router.get("/{asset_id}")
def get_asset(asset_id: str):
    """Get an asset by ID."""
    return {"id": asset_id}


@router.patch("/{asset_id}")
def update_asset(asset_id: str):
    """Update an asset."""
    return {"id": asset_id}


@router.delete("/{asset_id}")
def delete_asset(asset_id: str):
    """Delete an asset."""
    return {"message": "Deleted"}


@router.post("/{asset_id}/relations")
def add_asset_relation(asset_id: str):
    """Add a relation to an asset."""
    return {}


@router.delete("/{asset_id}/relations/{relation_id}")
def delete_asset_relation(asset_id: str, relation_id: str):
    """Delete an asset relation."""
    return {"message": "Deleted"}