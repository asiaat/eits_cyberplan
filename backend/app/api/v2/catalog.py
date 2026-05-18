"""Catalog and E-ITS reference data API v2.

E-ITS (Estonian Information Security Standard) Catalog API.
Provides access to security measures, modules, threats, and reference data.

Tags:
    - Catalog: E-ITS catalog version management
    - Modules: Security module CRUD operations
    - Measures: Security measure queries and filtering
    - Threats: E-ITS threat management
    - Reference: Damage scenarios and asset categories
"""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.deps import DB
from app.api.v2.auth import LocalUser, get_current_user_v2
from app.models.asset_type_category import AssetTypeCategory
from app.models.damage_scenario import DamageScenario
from app.models.eits_catalog_measure import EitsCatalogMeasure
from app.models.eits_catalog_version import EitsCatalogVersion
from app.models.eits_module import EitsModule
from app.models.eits_threat import EitsThreat, ModuleThreat
from app.schemas.eits_catalog import (
    AssetTypeCategoryResponse,
    CatalogVersionResponse,
    DamageScenarioResponse,
    EitsCatalogMeasureResponse,
    EitsModuleResponse,
    EitsThreatResponse,
    ModuleThreatCreate,
    ModuleThreatResponse,
)

router = APIRouter(tags=["Catalog"])


@router.get(
    "/versions",
    response_model=list[CatalogVersionResponse],
    summary="List catalog versions",
    description="Retrieve all E-ITS catalog versions. Optionally filter for active versions only.",
    tags=["Catalog"],
)
def list_catalog_versions(
    db: DB,
    current_user: LocalUser = Depends(get_current_user_v2),
    active_only: bool = Query(False, alias="active_only", description="Filter to only active (released) versions"),
):
    """List E-ITS catalog versions.

    Returns all available E-ITS catalog versions ordered by import date (newest first).
    Use `active_only=true` to return only versions marked as active/released.
    """
    query = db.query(EitsCatalogVersion)
    if active_only:
        query = query.filter(EitsCatalogVersion.is_active)
    versions = query.order_by(EitsCatalogVersion.imported_at.desc()).all()
    return versions


@router.get(
    "/versions/{version_id}",
    response_model=CatalogVersionResponse,
    summary="Get catalog version",
    description="Retrieve a specific E-ITS catalog version by its unique identifier.",
    tags=["Catalog"],
)
def get_catalog_version(
    version_id: UUID,
    db: DB,
    current_user: LocalUser = Depends(get_current_user_v2),
):
    """Get a catalog version by ID.

    Args:
        version_id: UUID of the catalog version to retrieve.

    Returns:
        CatalogVersionResponse with version details including year, name, and status.

    Raises:
        404: If catalog version is not found.
    """
    version = db.query(EitsCatalogVersion).filter(
        EitsCatalogVersion.id == version_id
    ).first()
    if not version:
        raise HTTPException(status_code=404, detail="Catalog version not found")
    return version


@router.get(
    "/versions/{version_id}/modules",
    response_model=list[EitsModuleResponse],
    summary="List modules by version",
    description="Retrieve all E-ITS modules belonging to a specific catalog version.",
    tags=["Modules"],
)
def list_modules_by_version(
    version_id: UUID,
    db: DB,
    current_user: LocalUser = Depends(get_current_user_v2),
    module_group: str | None = Query(None, alias="module_group", description="Filter by module group (e.g., ISMS, ORP, INF)"),
    module_type: str | None = Query(None, alias="module_type", description="Filter by type: PROCESS or SYSTEM"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(200, ge=1, le=500, description="Maximum number of records to return"),
):
    """List E-ITS modules for a specific catalog version.

    Args:
        version_id: UUID of the catalog version.
        module_group: Optional filter for module group (ISMS, ORP, CON, OPS, DER, INF, NET, SYS, APP, IND).
        module_type: Optional filter for module type (PROCESS/SYSTEM).
        skip: Pagination offset.
        limit: Maximum results per page (max 500).

    Returns:
        List of EitsModuleResponse objects.
    """
    query = db.query(EitsModule).filter(EitsModule.catalog_version_id == version_id)
    if module_group:
        query = query.filter(EitsModule.module_group == module_group)
    if module_type:
        query = query.filter(EitsModule.module_type == module_type)
    modules = query.offset(skip).limit(limit).all()
    return modules


@router.get(
    "/modules",
    response_model=list[EitsModuleResponse],
    summary="List all modules",
    description="Retrieve all E-ITS modules across all catalog versions with optional filtering.",
    tags=["Modules"],
)
def list_all_modules(
    db: DB,
    current_user: LocalUser = Depends(get_current_user_v2),
    version_id: UUID | None = Query(None, alias="version_id", description="Filter by specific catalog version"),
    module_group: str | None = Query(None, alias="module_group", description="Filter by module group"),
    module_type: str | None = Query(None, alias="module_type", description="Filter by type: PROCESS or SYSTEM"),
    skip: int = Query(0, ge=0),
    limit: int = Query(500, ge=1, le=1000),
):
    """List all E-ITS modules with optional filtering.

    Args:
        version_id: Optional catalog version filter.
        module_group: Optional module group filter.
        module_type: Optional module type filter.
        skip: Pagination offset.
        limit: Maximum results (max 1000).

    Returns:
        List of EitsModuleResponse objects.
    """
    query = db.query(EitsModule)
    if version_id:
        query = query.filter(EitsModule.catalog_version_id == version_id)
    if module_group:
        query = query.filter(EitsModule.module_group == module_group)
    if module_type:
        query = query.filter(EitsModule.module_type == module_type)
    modules = query.offset(skip).limit(limit).all()
    return modules


@router.get(
    "/modules/{module_id}",
    response_model=EitsModuleResponse,
    summary="Get module details",
    description="Retrieve a single E-ITS module by its unique identifier.",
    tags=["Modules"],
)
def get_module(
    module_id: UUID,
    db: DB,
    current_user: LocalUser = Depends(get_current_user_v2),
):
    """Get a module by ID.

    Args:
        module_id: UUID of the module to retrieve.

    Returns:
        EitsModuleResponse with module details.

    Raises:
        404: If module is not found.
    """
    module = db.query(EitsModule).filter(EitsModule.id == module_id).first()
    if not module:
        raise HTTPException(status_code=404, detail="Module not found")
    return module


@router.get(
    "/modules/{module_id}/measures",
    response_model=list[EitsCatalogMeasureResponse],
    summary="List module measures",
    description="Get all security measures belonging to a specific E-ITS module.",
    tags=["Measures"],
)
def list_module_measures(
    module_id: UUID,
    db: DB,
    current_user: LocalUser = Depends(get_current_user_v2),
    level: str | None = Query(None, alias="level", description="Filter by measure level: BASE, STANDARD, or HIGH"),
):
    """List measures for a specific module.

    Args:
        module_id: UUID of the module.
        level: Optional filter by measure level (BASE/STANDARD/HIGH).

    Returns:
        List of EitsCatalogMeasureResponse objects.

    Raises:
        404: If module is not found.
    """
    module = db.query(EitsModule).filter(EitsModule.id == module_id).first()
    if not module:
        raise HTTPException(status_code=404, detail="Module not found")

    query = db.query(EitsCatalogMeasure).filter(EitsCatalogMeasure.module_id == module_id)
    if level:
        query = query.filter(EitsCatalogMeasure.measure_level == level)
    measures = query.all()
    return measures


@router.get(
    "/measures",
    response_model=list[EitsCatalogMeasureResponse],
    summary="List all measures",
    description="Retrieve all E-ITS security measures with optional filtering by version, level, or module group.",
    tags=["Measures"],
)
def list_all_measures(
    db: DB,
    current_user: LocalUser = Depends(get_current_user_v2),
    version_id: UUID | None = Query(None, alias="version_id", description="Filter by catalog version"),
    level: str | None = Query(None, alias="level", description="Filter by measure level: BASE, STANDARD, HIGH"),
    module_group: str | None = Query(None, alias="module_group", description="Filter by module group"),
    skip: int = Query(0, ge=0),
    limit: int = Query(500, ge=1, le=1000),
):
    """List all E-ITS measures with optional filtering.

    Args:
        version_id: UUID of the catalog version to filter by.
        level: Measure level filter (BASE/STANDARD/HIGH).
        module_group: Module group filter (ISMS, ORP, INF, etc.).
        skip: Pagination offset.
        limit: Maximum results (max 1000).

    Returns:
        List of EitsCatalogMeasureResponse objects with code, name, level, and description.
    """
    query = db.query(EitsCatalogMeasure).join(EitsModule)

    if version_id:
        query = query.filter(EitsModule.catalog_version_id == version_id)
    if level:
        query = query.filter(EitsCatalogMeasure.measure_level == level)
    if module_group:
        query = query.filter(EitsModule.module_group == module_group)

    measures = query.offset(skip).limit(limit).all()
    return measures


@router.get(
    "/measures/levels",
    summary="Get measure levels",
    description="Returns the available E-ITS measure security levels.",
    tags=["Measures"],
)
def list_measure_levels(
    current_user: LocalUser = Depends(get_current_user_v2),
):
    """Get available measure levels.

    Returns:
        List of available measure level values: BASE, STANDARD, HIGH.
    """
    return ["BASE", "STANDARD", "HIGH"]


@router.get(
    "/threats",
    response_model=list[EitsThreatResponse],
    summary="List threats",
    description="Retrieve E-ITS threats with optional filtering by version or category.",
    tags=["Threats"],
)
def list_threats(
    db: DB,
    current_user: LocalUser = Depends(get_current_user_v2),
    version_id: UUID | None = Query(None, alias="version_id", description="Filter by catalog version"),
    category: str | None = None,
):
    """List E-ITS threats.

    Args:
        version_id: Optional filter by catalog version UUID.
        category: Optional filter by threat category.

    Returns:
        List of EitsThreatResponse objects.
    """
    query = db.query(EitsThreat)
    if version_id:
        query = query.filter(EitsThreat.version_id == version_id)
    if category:
        query = query.filter(EitsThreat.category == category)
    return query.all()


@router.post(
    "/module-threats",
    response_model=ModuleThreatResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Link threat to module",
    description="Associate an E-ITS threat with a specific security module.",
    tags=["Threats"],
)
def create_module_threat(
    db: DB,
    current_user: LocalUser = Depends(get_current_user_v2),
    data: ModuleThreatCreate = None,
):
    """Link a threat to a module.

    Args:
        data: ModuleThreatCreate with module_id, threat_id, and optional relevance_note.

    Returns:
        ModuleThreatResponse with the created link.

    Raises:
        400: If threat is already linked to the module.
        400: If request body is missing.
    """
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


@router.delete(
    "/module-threats/{mt_id}",
    summary="Remove threat link",
    description="Remove the association between a threat and a module.",
    tags=["Threats"],
)
def delete_module_threat(
    mt_id: UUID,
    db: DB,
    current_user: LocalUser = Depends(get_current_user_v2),
):
    """Remove a threat from a module.

    Args:
        mt_id: UUID of the module-threat link to remove.

    Returns:
        Confirmation message.

    Raises:
        404: If module-threat link is not found.
    """
    mt = db.query(ModuleThreat).filter(ModuleThreat.id == mt_id).first()
    if not mt:
        raise HTTPException(status_code=404, detail="Module-threat link not found")
    db.delete(mt)
    db.commit()
    return {"message": "Link removed"}


@router.get(
    "/damage-scenarios",
    response_model=list[DamageScenarioResponse],
    summary="List damage scenarios",
    description="Retrieve all E-ITS damage scenarios (KS1-KS6) used in risk assessment.",
    tags=["Reference"],
)
def list_damage_scenarios(
    db: DB,
    current_user: LocalUser = Depends(get_current_user_v2),
):
    """List all damage scenarios (KS1-KS6).

    Damage scenarios represent categories of potential harm:
    - KS1: Legal compliance breach
    - KS2: Privacy violation
    - KS3: Physical damage
    - KS4: Task disruption
    - KS5: Reputation damage
    - KS6: Financial losses

    Returns:
        List of DamageScenarioResponse objects.
    """
    return db.query(DamageScenario).all()


@router.get(
    "/asset-categories",
    response_model=list[AssetTypeCategoryResponse],
    summary="List asset categories",
    description="Retrieve all E-ITS asset type categories for classification.",
    tags=["Reference"],
)
def list_asset_categories(
    db: DB,
    current_user: LocalUser = Depends(get_current_user_v2),
):
    """List all asset type categories (T/V/I/R/A).

    Categories:
    - T: Infrastructure (buildings, rooms, technical systems)
    - V: Network components (LAN, WAN, WLAN, VPN, firewalls)
    - I: IT systems (servers, clients, laptops, mobile devices)
    - R: Applications (software, databases, web services, email)
    - A: Industrial automation (PLC, SCADA, ICS controllers)

    Returns:
        List of AssetTypeCategoryResponse objects.
    """
    return db.query(AssetTypeCategory).all()
