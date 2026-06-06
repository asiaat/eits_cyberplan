"""Dashboard API endpoints v2."""
from datetime import date
from typing import List
from uuid import UUID

from fastapi import APIRouter, Query
from sqlalchemy.orm import Session, joinedload

from app.api.deps import DB
from app.api.v2.auth import CurrentUserV2, LocalUser
from app.models.alert import Alert
from app.models.business_process import BusinessProcess
from app.models.evidence_link import EvidenceLink
from app.models.imr_item import ImrItem
from app.models.local_user import LocalUser
from app.models.risk import Risk

router = APIRouter()


@router.get("/summary", response_model=dict)
def dashboard_summary_v2(
    db: DB,
    current_user: LocalUser = CurrentUserV2,
):
    """Get comprehensive dashboard summary with key metrics."""
    tenant_id = current_user.tenant_id

    total_imr_items = db.query(ImrItem).filter(
        ImrItem.tenant_id == tenant_id,
        ImrItem.imr_snapshot_id.is_(None),
    ).count()

    implemented_items = db.query(ImrItem).filter(
        ImrItem.tenant_id == tenant_id,
        ImrItem.imr_snapshot_id.is_(None),
        ImrItem.pearo_status == "R",
    ).count()

    in_progress_items = db.query(ImrItem).filter(
        ImrItem.tenant_id == tenant_id,
        ImrItem.imr_snapshot_id.is_(None),
        ImrItem.pearo_status == "E",
    ).count()

    not_started_items = db.query(ImrItem).filter(
        ImrItem.tenant_id == tenant_id,
        ImrItem.imr_snapshot_id.is_(None),
        ImrItem.pearo_status == "U",
    ).count()

    today = date.today()
    overdue_items = db.query(ImrItem).filter(
        ImrItem.tenant_id == tenant_id,
        ImrItem.imr_snapshot_id.is_(None),
        ImrItem.due_date < today,
        ImrItem.pearo_status != "R",
    ).count()

    high_risks = db.query(Risk).filter(
        Risk.tenant_id == tenant_id,
        Risk.risk_level.in_(["high", "very_high"]),
    ).count()

    implemented_ids = db.query(ImrItem.id).filter(
        ImrItem.tenant_id == tenant_id,
        ImrItem.imr_snapshot_id.is_(None),
        ImrItem.pearo_status == "R",
    ).subquery()

    linked_evidence = db.query(EvidenceLink.target_id).filter(
        EvidenceLink.tenant_id == tenant_id,
        EvidenceLink.target_type == "imr_item",
        EvidenceLink.target_id.in_(db.query(implemented_ids.c.id)),
    ).subquery()

    items_without_evidence = db.query(ImrItem).filter(
        ImrItem.tenant_id == tenant_id,
        ImrItem.imr_snapshot_id.is_(None),
        ImrItem.pearo_status == "R",
        ~ImrItem.id.in_(db.query(linked_evidence.c.target_id)),
    ).count()

    imr_completion_percentage = 0
    if total_imr_items > 0:
        imr_completion_percentage = round((implemented_items / total_imr_items) * 100, 1)

    audit_readiness_score = 0
    if total_imr_items > 0:
        evidence_ratio = (implemented_items - items_without_evidence) / implemented_items if implemented_items > 0 else 0
        risk_factor = 1.0 - (high_risks / max(total_imr_items, 1)) * 0.3
        audit_readiness_score = round((imr_completion_percentage / 100) * evidence_ratio * 100 * risk_factor, 1)

    return {
        "total_imr_items": total_imr_items,
        "implemented_items": implemented_items,
        "in_progress_items": in_progress_items,
        "not_started_items": not_started_items,
        "overdue_items": overdue_items,
        "high_risks": high_risks,
        "items_without_evidence": items_without_evidence,
        "imr_completion_percentage": imr_completion_percentage,
        "audit_readiness_score": audit_readiness_score,
    }


@router.get("/imr-progress", response_model=dict)
def imr_progress_v2(
    db: DB,
    current_user: LocalUser = CurrentUserV2,
):
    """Get detailed IMR progress breakdown."""
    tenant_id = current_user.tenant_id

    u = db.query(ImrItem).filter(ImrItem.tenant_id == tenant_id, ImrItem.imr_snapshot_id.is_(None), ImrItem.pearo_status == "U").count()
    p = db.query(ImrItem).filter(ImrItem.tenant_id == tenant_id, ImrItem.imr_snapshot_id.is_(None), ImrItem.pearo_status == "P").count()
    e = db.query(ImrItem).filter(ImrItem.tenant_id == tenant_id, ImrItem.imr_snapshot_id.is_(None), ImrItem.pearo_status == "E").count()
    a = db.query(ImrItem).filter(ImrItem.tenant_id == tenant_id, ImrItem.imr_snapshot_id.is_(None), ImrItem.pearo_status == "A").count()
    r = db.query(ImrItem).filter(ImrItem.tenant_id == tenant_id, ImrItem.imr_snapshot_id.is_(None), ImrItem.pearo_status == "R").count()
    o = db.query(ImrItem).filter(ImrItem.tenant_id == tenant_id, ImrItem.imr_snapshot_id.is_(None), ImrItem.pearo_status == "O").count()

    total = u + p + e + a + r + o

    def safe_percent(count):
        return round((count / total) * 100, 1) if total > 0 else 0

    return {
        "not_started": u,
        "in_progress": e,
        "implemented": r,
        "not_applicable": p,
        "accepted_exception": a,
        "needs_review": o,
        "total": total,
        "percentages": {
            "not_started": safe_percent(u),
            "in_progress": safe_percent(e),
            "implemented": safe_percent(r),
            "not_applicable": safe_percent(p),
            "accepted_exception": safe_percent(a),
            "needs_review": safe_percent(o),
        },
    }


@router.get("/risk-heatmap", response_model=dict)
def risk_heatmap_v2(
    db: DB,
    current_user: LocalUser = CurrentUserV2,
):
    """Get risk heatmap data showing protection needs vs risks."""
    tenant_id = current_user.tenant_id

    business_processes = db.query(BusinessProcess).filter(
        BusinessProcess.tenant_id == tenant_id
    ).all()

    protection_needs = ["normal", "high", "very_high", "unknown"]
    risk_levels = ["low", "medium", "high", "very_high"]

    heatmap_data = []
    for pn in protection_needs:
        row = {"protection_need": pn, "data": []}
        for _rl in risk_levels:
            row["data"].append(0)
        heatmap_data.append(row)

    risk_level_map = {
        "low": 0,
        "medium": 1,
        "high": 2,
        "very_high": 3,
    }

    protection_need_map = {
        "normal": 0,
        "high": 1,
        "very_high": 2,
        "unknown": 3,
    }

    for bp in business_processes:
        pn_idx = max(
            protection_need_map.get(bp.confidentiality_need, 3),
            protection_need_map.get(bp.integrity_need, 3),
            protection_need_map.get(bp.availability_need, 3),
        )

        risks = db.query(Risk).filter(
            Risk.tenant_id == tenant_id,
            Risk.target_type == "business_process",
            Risk.target_id == bp.id,
        ).all()

        if risks:
            risk_order = ["low", "medium", "high", "very_high"]
            highest_risk = max(risks, key=lambda r: risk_order.index(r.risk_level) if r.risk_level in risk_order else 0)
            risk_idx = risk_level_map.get(highest_risk.risk_level, 0)
        else:
            risk_idx = 0

        if 0 <= pn_idx < len(heatmap_data) and 0 <= risk_idx < len(heatmap_data[pn_idx]["data"]):
            heatmap_data[pn_idx]["data"][risk_idx] += 1

    formatted_data = []
    for row in heatmap_data:
        formatted_data.append({
            "protection_need": row["protection_need"],
            "low": row["data"][0],
            "medium": row["data"][1],
            "high": row["data"][2],
            "very_high": row["data"][3],
        })

    return {
        "protection_needs": protection_needs,
        "risk_levels": risk_levels,
        "data": formatted_data,
        "total_business_processes": len(business_processes),
    }


@router.get("/alerts/current", response_model=List[dict])
def get_current_alerts_v2(
    db: DB,
    current_user: LocalUser = CurrentUserV2,
    limit: int = Query(50, ge=1, le=100),
):
    """Get current active alerts for the dashboard."""
    from app.models.local_user import EITSRole, UserRole

    user_roles = db.query(UserRole).filter(UserRole.user_id == current_user.id).all()
    role_ids = [ur.role_id for ur in user_roles]
    roles = db.query(EITSRole).filter(EITSRole.id.in_(role_ids)).all() if role_ids else []
    role_names = [r.role_name for r in roles]

    target_roles = ["all"]
    if any(r in ["Infoturbejuht", "Juhtkond", "admin"] for r in role_names):
        target_roles.extend(["admin", "ism"])

    alerts = db.query(Alert).filter(
        Alert.is_active == "true",
        Alert.target_role.in_(target_roles),
    ).order_by(Alert.created_at.desc()).limit(limit).all()

    return [
        {
            "id": str(a.id),
            "title": a.title,
            "message": a.message,
            "level": a.level,
            "is_read": a.is_read or False,
            "created_at": str(a.created_at),
            "link": a.link,
        }
        for a in alerts
    ]


@router.get("/alerts/history", response_model=List[dict])
def get_alert_history_v2(
    db: DB,
    current_user: LocalUser = CurrentUserV2,
    limit: int = Query(100, ge=1, le=200),
):
    """Get alert history for the dashboard."""
    alerts = db.query(Alert).order_by(Alert.created_at.desc()).limit(limit).all()

    return [
        {
            "id": str(a.id),
            "title": a.title,
            "message": a.message,
            "level": a.level,
            "is_read": a.is_read or False,
            "created_at": str(a.created_at),
            "link": a.link,
        }
        for a in alerts
    ]
