"""Tenants API endpoints."""
from fastapi import APIRouter, Depends

router = APIRouter()


@router.get("/current")
def get_current_tenant():
    """Get current tenant."""
    return {"id": "default", "name": "Default Organization"}