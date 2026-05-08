"""E-ITS Catalog API endpoints."""
from typing import List

from fastapi import APIRouter, Depends, Query

from app.api.deps import DB, CurrentUser

router = APIRouter()


@router.get("/versions")
def list_catalog_versions(db: DB, current_user: CurrentUser):
    """List catalog versions."""
    from app.models.eits_catalog_version import EitsCatalogVersion
    return db.query(EitsCatalogVersion).all()


@router.get("/modules")
def list_modules(
    db: DB,
    current_user: CurrentUser,
    catalog_version_id: str | None = Query(None),
    search: str | None = Query(None),
):
    """List E-ITS modules."""
    from app.models.eits_module import EitsModule
    return db.query(EitsModule).all()


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