"""Catalog and E-ITS reference data API v2."""
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload

from app.api.deps import DB
from app.api.v2.auth import get_current_user_v2, LocalUser
from app.models.eits_catalog_version import EitsCatalogVersion
from app.models.eits_module import EitsModule
from app.models.eits_catalog_measure import EitsCatalogMeasure
from app.models.eits_threat import EitsThreat, ModuleThreat
from app.models.damage_scenario import DamageScenario
from app.models.asset_type_category import AssetTypeCategory
from app.schemas.eits_catalog import (
    CatalogVersionResponse,
    EitsModuleResponse,
    EitsModuleWithMeasures,
    EitsCatalogMeasureResponse,
    EitsThreatResponse,
    ModuleThreatCreate,
    ModuleThreatResponse,
    DamageScenarioResponse,
    AssetTypeCategoryResponse,
)

router = APIRouter()


@router.get("/versions", response_model=list[CatalogVersionResponse])
def list_catalog_versions(
    db: DB,
    current_user: LocalUser = Depends(get_current_user_v2),
    active_only: bool = Query(False, alias="active_only"),
):
    """List E-ITS catalog versions."""
    query = db.query(EitsCatalogVersion)
    if active_only:
        query = query.filter(EitsCatalogVersion.is_active == True)
    versions = query.order_by(EitsCatalogVersion.imported_at.desc()).all()
    return versions


@router.get("/versions/{version_id}", response_model=CatalogVersionResponse)
def get_catalog_version(
    version_id: UUID,
    db: DB,
    current_user: LocalUser = Depends(get_current_user_v2),
):
    """Get a catalog version by ID."""
    version = db.query(EitsCatalogVersion).filter(
        EitsCatalogVersion.id == version_id
    ).first()
    if not version:
        raise HTTPException(status_code=404, detail="Catalog version not found")
    return version


@router.get("/versions/{version_id}/modules", response_model=list[EitsModuleResponse])
def list_modules_by_version(
    version_id: UUID,
    db: DB,
    current_user: LocalUser = Depends(get_current_user_v2),
    module_group: Optional[str] = Query(None, alias="module_group"),
    module_type: Optional[str] = Query(None, alias="module_type"),
    skip: int = Query(0, ge=0),
    limit: int = Query(200, ge=1, le=500),
):
    """List E-ITS modules for a specific catalog version."""
    query = db.query(EitsModule).filter(EitsModule.catalog_version_id == version_id)
    if module_group:
        query = query.filter(EitsModule.module_group == module_group)
    if module_type:
        query = query.filter(EitsModule.module_type == module_type)
    modules = query.offset(skip).limit(limit).all()
    return modules


@router.get("/modules/{module_id}", response_model=EitsModuleResponse)
def get_module(
    module_id: UUID,
    db: DB,
    current_user: LocalUser = Depends(get_current_user_v2),
):
    """Get a module by ID."""
    module = db.query(EitsModule).filter(EitsModule.id == module_id).first()
    if not module:
        raise HTTPException(status_code=404, detail="Module not found")
    return module


@router.get("/modules/{module_id}/measures", response_model=list[EitsCatalogMeasureResponse])
def list_module_measures(
    module_id: UUID,
    db: DB,
    current_user: LocalUser = Depends(get_current_user_v2),
    level: Optional[str] = Query(None, alias="level"),
):
    """List measures for a specific module."""
    module = db.query(EitsModule).filter(EitsModule.id == module_id).first()
    if not module:
        raise HTTPException(status_code=404, detail="Module not found")

    query = db.query(EitsCatalogMeasure).filter(EitsCatalogMeasure.module_id == module_id)
    if level:
        query = query.filter(EitsCatalogMeasure.measure_level == level)
    measures = query.all()
    return measures


@router.get("/measures", response_model=list[EitsCatalogMeasureResponse])
def list_all_measures(
    db: DB,
    current_user: LocalUser = Depends(get_current_user_v2),
    version_id: Optional[UUID] = Query(None, alias="version_id"),
    level: Optional[str] = Query(None, alias="level"),
    module_group: Optional[str] = Query(None, alias="module_group"),
    skip: int = Query(0, ge=0),
    limit: int = Query(500, ge=1, le=1000),
):
    """List all E-ITS measures with optional filtering."""
    query = db.query(EitsCatalogMeasure).join(EitsModule)

    if version_id:
        query = query.filter(EitsModule.catalog_version_id == version_id)
    if level:
        query = query.filter(EitsCatalogMeasure.measure_level == level)
    if module_group:
        query = query.filter(EitsModule.module_group == module_group)

    measures = query.offset(skip).limit(limit).all()
    return measures


@router.get("/threats", response_model=list[EitsThreatResponse])
def list_threats(
    db: DB,
    current_user: LocalUser = Depends(get_current_user_v2),
    version_id: Optional[UUID] = Query(None, alias="version_id"),
    category: Optional[str] = None,
):
    """List E-ITS threats."""
    query = db.query(EitsThreat)
    if version_id:
        query = query.filter(EitsThreat.version_id == version_id)
    if category:
        query = query.filter(EitsThreat.category == category)
    return query.all()


@router.post("/module-threats", response_model=ModuleThreatResponse, status_code=status.HTTP_201_CREATED)
def create_module_threat(
    db: DB,
    current_user: LocalUser = Depends(get_current_user_v2),
    data: ModuleThreatCreate = None,
):
    """Link a threat to a module."""
    if data is None:
        raise HTTPException(status_code=400, detail="Request body required")

    existing = db.query(ModuleThreat).filter(
        ModuleThreat.module_id == data.module_id,
        ModuleThreat.threat_id == data.threat_id,
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Threat already linked to this module")

    mt = ModuleThreat(
        module_id=data.module_id,
        threat_id=data.threat_id,
        relevance_note=data.relevance_note,
    )
    db.add(mt)
    db.commit()
    db.refresh(mt)
    return mt


@router.delete("/module-threats/{mt_id}")
def delete_module_threat(
    mt_id: UUID,
    db: DB,
    current_user: LocalUser = Depends(get_current_user_v2),
):
    """Remove a threat from a module."""
    mt = db.query(ModuleThreat).filter(ModuleThreat.id == mt_id).first()
    if not mt:
        raise HTTPException(status_code=404, detail="Module-threat link not found")
    db.delete(mt)
    db.commit()
    return {"message": "Link removed"}


@router.get("/damage-scenarios", response_model=list[DamageScenarioResponse])
def list_damage_scenarios(
    db: DB,
    current_user: LocalUser = Depends(get_current_user_v2),
):
    """List all damage scenarios (KS1-KS6)."""
    return db.query(DamageScenario).all()


@router.get("/asset-categories", response_model=list[AssetTypeCategoryResponse])
def list_asset_categories(
    db: DB,
    current_user: LocalUser = Depends(get_current_user_v2),
):
    """List all asset type categories (T/V/I/R/A)."""
    return db.query(AssetTypeCategory).all()