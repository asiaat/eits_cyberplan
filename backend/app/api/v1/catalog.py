"""E-ITS Catalog API endpoints."""
from typing import List

from fastapi import APIRouter, Depends, Query

router = APIRouter()


@router.get("/versions")
def list_catalog_versions():
    """List catalog versions."""
    return []


@router.get("/modules")
def list_modules(
    catalog_version_id: str | None = Query(None),
    search: str | None = Query(None),
):
    """List E-ITS modules."""
    return []


@router.get("/modules/{module_id}")
def get_module(module_id: str):
    """Get a module by ID."""
    return {"id": module_id}


@router.get("/measures")
def list_measures(
    module_id: str | None = Query(None),
    search: str | None = Query(None),
):
    """List E-ITS measures."""
    return []


@router.get("/measures/{measure_id}")
def get_measure(measure_id: str):
    """Get a measure by ID."""
    return {"id": measure_id}


@router.get("/modules/{module_id}/measures")
def get_module_measures(module_id: str):
    """Get measures for a module."""
    return []