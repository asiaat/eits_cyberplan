"""Business Processes API endpoints."""
from typing import List

from fastapi import APIRouter, Depends

router = APIRouter()


@router.get("/")
def list_business_processes():
    """List business processes."""
    return []


@router.post("/")
def create_business_process():
    """Create a business process."""
    return {}


@router.get("/{process_id}")
def get_business_process(process_id: str):
    """Get a business process by ID."""
    return {"id": process_id}


@router.patch("/{process_id}")
def update_business_process(process_id: str):
    """Update a business process."""
    return {"id": process_id}


@router.delete("/{process_id}")
def delete_business_process(process_id: str):
    """Delete a business process."""
    return {"message": "Deleted"}


@router.post("/{process_id}/assets")
def add_process_asset(process_id: str):
    """Add an asset to a process."""
    return {}


@router.delete("/{process_id}/assets/{asset_id}")
def remove_process_asset(process_id: str, asset_id: str):
    """Remove an asset from a process."""
    return {"message": "Removed"}