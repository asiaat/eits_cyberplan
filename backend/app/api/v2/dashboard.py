"""Dashboard API v2 — aggregate stats for the dashboard view."""
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import DB
from app.api.v2.auth import get_current_user_v2, LocalUser
from app.models.business_process import BusinessProcess
from app.models.asset import Asset
from app.models.protectionmode_selection import ProtectionModeSelection
from app.services.v2.imr_regeneration_service import ImrRegenerationService

router = APIRouter()


class BusinessProcessStats(BaseModel):
    total: int
    by_status: dict[str, int]
    by_protection_need: dict[str, int]


class AssetStats(BaseModel):
    total: int
    by_type: dict[str, int]
    by_criticality: dict[str, int]
    by_lifecycle_status: dict[str, int]


class ScopeStats(BaseModel):
    active_approach: str | None = None
    modules_count: int = 0
    measures_count: int = 0


class DashboardStatsResponse(BaseModel):
    business_processes: BusinessProcessStats
    assets: AssetStats
    scope: ScopeStats


@router.get("/dashboard/stats", response_model=DashboardStatsResponse)
def get_dashboard_stats(
    db: DB,
    current_user: LocalUser = Depends(get_current_user_v2),
):
    """Aggregate dashboard statistics for business processes, assets, and scope."""
    tenant_id = current_user.tenant_id

    # --- Business Process stats ---
    bp_query = db.query(BusinessProcess).filter(
        BusinessProcess.tenant_id == tenant_id,
        BusinessProcess.deleted_at.is_(None),
    )

    bp_total = bp_query.count()

    bp_by_status = dict(
        db.query(BusinessProcess.status, func.count(BusinessProcess.id))
        .filter(
            BusinessProcess.tenant_id == tenant_id,
            BusinessProcess.deleted_at.is_(None),
        )
        .group_by(BusinessProcess.status)
        .all()
    )

    # Protection need is MAX of C, I, A — we just aggregate by individual dimensions
    bp_by_protection_need: dict[str, int] = {"normal": 0, "high": 0, "very_high": 0, "unknown": 0}
    bp_need_rows = db.query(
        BusinessProcess.confidentiality_need,
        BusinessProcess.integrity_need,
        BusinessProcess.availability_need,
    ).filter(
        BusinessProcess.tenant_id == tenant_id,
        BusinessProcess.deleted_at.is_(None),
    ).all()

    for c, i, a in bp_need_rows:
        from app.services.business_process_service import ProtectionNeedLevel
        overall = ProtectionNeedLevel.max_level(c or "unknown", i or "unknown", a or "unknown")
        bp_by_protection_need[overall] = bp_by_protection_need.get(overall, 0) + 1

    # --- Asset stats ---
    asset_query = db.query(Asset).filter(
        Asset.tenant_id == tenant_id,
        Asset.deleted_at.is_(None),
    )

    asset_total = asset_query.count()

    asset_by_type = dict(
        db.query(Asset.asset_type, func.count(Asset.id))
        .filter(
            Asset.tenant_id == tenant_id,
            Asset.deleted_at.is_(None),
        )
        .group_by(Asset.asset_type)
        .all()
    )

    asset_by_criticality = dict(
        db.query(Asset.criticality, func.count(Asset.id))
        .filter(
            Asset.tenant_id == tenant_id,
            Asset.deleted_at.is_(None),
        )
        .group_by(Asset.criticality)
        .all()
    )

    asset_by_lifecycle_status = dict(
        db.query(Asset.lifecycle_status, func.count(Asset.id))
        .filter(
            Asset.tenant_id == tenant_id,
            Asset.deleted_at.is_(None),
        )
        .group_by(Asset.lifecycle_status)
        .all()
    )

    # --- Scope stats ---
    active_selection = db.query(ProtectionModeSelection).filter(
        ProtectionModeSelection.tenant_id == tenant_id,
        ProtectionModeSelection.is_active.is_(True),
        ProtectionModeSelection.deleted_at.is_(None),
    ).first()

    scope = ScopeStats()
    if active_selection:
        try:
            preview = ImrRegenerationService.get_approach_stats(db, active_selection.security_approach)
            scope.active_approach = active_selection.security_approach
            scope.modules_count = preview.get("modules_count", 0)
            scope.measures_count = preview.get("measures_count", 0)
        except Exception:
            scope.active_approach = active_selection.security_approach

    return DashboardStatsResponse(
        business_processes=BusinessProcessStats(
            total=bp_total,
            by_status=bp_by_status,
            by_protection_need=bp_by_protection_need,
        ),
        assets=AssetStats(
            total=asset_total,
            by_type=asset_by_type,
            by_criticality=asset_by_criticality,
            by_lifecycle_status=asset_by_lifecycle_status,
        ),
        scope=scope,
    )
