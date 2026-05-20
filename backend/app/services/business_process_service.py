"""Business Process Service - E-ITS SOPs for protection needs and dependencies."""
from typing import Optional
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.business_process import BusinessProcess
from app.models.business_process_dependency import BusinessProcessDependency
from app.models.alert import Alert
from app.models.local_user import EITSRole, UserRole, LocalUser


class ProtectionNeedLevel(str):
    NORMAL = "normal"
    HIGH = "high"
    VERY_HIGH = "very_high"
    UNKNOWN = "unknown"

    @staticmethod
    def get_order(level: str) -> int:
        order = {
            "unknown": 0,
            "normal": 1,
            "high": 2,
            "very_high": 3,
        }
        return order.get(level.lower(), 0)

    @staticmethod
    def max_level(c: str, i: str, a: str) -> str:
        levels = ["unknown", "normal", "high", "very_high"]
        c_order = ProtectionNeedLevel.get_order(c)
        i_order = ProtectionNeedLevel.get_order(i)
        a_order = ProtectionNeedLevel.get_order(a)
        max_order = max(c_order, i_order, a_order)
        return levels[max_order]


def calculate_protection_need(
    confidentiality: str,
    integrity: str,
    availability: str
) -> str:
    """SOP 1: Calculate overall protection need as MAX of C, I, A dimensions."""
    return ProtectionNeedLevel.max_level(confidentiality, integrity, availability)


def is_high_or_very_high(level: str) -> bool:
    """Check if protection need level is HIGH or VERY_HIGH."""
    return level.lower() in ("high", "very_high")


def get_linked_asset_ids(db: Session, business_process_id: UUID) -> list[UUID]:
    """Get all asset IDs linked to a business process."""
    from app.models.process_asset import ProcessAsset
    links = db.query(ProcessAsset).filter(
        ProcessAsset.business_process_id == business_process_id
    ).all()
    return [link.asset_id for link in links]


def create_cascade_alert(
    db: Session,
    tenant_id: UUID,
    business_process_id: UUID,
    business_process_name: str,
    protection_need: str,
    asset_ids: list[UUID],
) -> Alert:
    """SOP 3: Create cascade alert for ISM when BP upgraded to HIGH/VERY_HIGH.

    Creates alerts for all assets linked to the BP to review their protection needs.
    """
    from app.models.asset import Asset

    alert = Alert(
        title=f"Asset Protection Review Required: {business_process_name}",
        message=f"Business process '{business_process_name}' has been assigned {protection_need.upper()} protection need. "
                f"Please review protection needs for all linked assets.",
        level="warning",
        target_role="ism",
        tenant_id=tenant_id,
        link=f"/assets?highlight=bp:{business_process_id}",
    )
    db.add(alert)

    for asset_id in asset_ids:
        asset_alert = Alert(
            title=f"Asset Review Required: {asset_id}",
            message=f"Asset is linked to BP '{business_process_name}' with {protection_need.upper()} protection. Review asset protection.",
            level="warning",
            target_role="ism",
            tenant_id=tenant_id,
        )
        db.add(asset_alert)

    return alert


def create_protection_need_alert(
    db: Session,
    tenant_id: UUID,
    business_process_id: UUID,
    business_process_name: str,
    old_protection_need: str,
    new_protection_need: str,
) -> Alert:
    """Create alert when BP protection need changes to HIGH/VERY_HIGH."""
    if not is_high_or_very_high(new_protection_need):
        return None

    alert = Alert(
        title=f"Business Process Protection Upgrade: {business_process_name}",
        message=f"Business process '{business_process_name}' protection need upgraded from {old_protection_need.upper()} to {new_protection_need.upper()}.",
        level="warning",
        target_role="ism",
        tenant_id=tenant_id,
        link=f"/processes/{business_process_id}",
    )
    db.add(alert)
    return alert


def check_circular_dependency(
    db: Session,
    business_process_id: UUID,
    new_dependency_id: UUID,
) -> bool:
    """Check if adding a dependency would create a circular reference."""
    visited = set()
    to_check = [new_dependency_id]
    
    while to_check:
        current_id = to_check.pop()
        if current_id == business_process_id:
            return True
        if current_id in visited:
            continue
        visited.add(current_id)
        
        deps = db.query(BusinessProcessDependency).filter(
            BusinessProcessDependency.business_process_id == current_id
        ).all()
        for dep in deps:
            if dep.depends_on_process_id:
                to_check.append(dep.depends_on_process_id)
    
    return False


def get_upstream_dependencies(
    db: Session,
    business_process_id: UUID,
    visited: set | None = None,
) -> list[dict]:
    """Get all upstream dependencies (processes this BP depends on)."""
    if visited is None:
        visited = set()
    
    if business_process_id in visited:
        return []
    visited.add(business_process_id)
    
    dependencies = db.query(BusinessProcessDependency).filter(
        BusinessProcessDependency.business_process_id == business_process_id
    ).all()
    
    result = []
    for dep in dependencies:
        if not dep.depends_on_process_id:
            continue
        bp = db.query(BusinessProcess).filter(BusinessProcess.id == dep.depends_on_process_id).first()
        result.append({
            "id": str(dep.id),
            "depends_on_process_id": str(dep.depends_on_process_id),
            "depends_on_process": {
                "id": str(bp.id) if bp else None,
                "name": bp.name if bp else "Unknown",
                "status": bp.status if bp else None,
            } if bp else None,
            "dependency_type": dep.dependency_type,
            "description": dep.description,
            "created_at": dep.created_at.isoformat() if dep.created_at else None,
        })
        # Recursively get upstream
        if bp:
            result.extend(get_upstream_dependencies(db, bp.id, visited))
    
    return result


def get_downstream_dependents(
    db: Session,
    business_process_id: UUID,
    visited: set | None = None,
) -> list[dict]:
    """Get all downstream dependents (processes that depend on this BP)."""
    if visited is None:
        visited = set()
    
    if business_process_id in visited:
        return []
    visited.add(business_process_id)
    
    dependencies = db.query(BusinessProcessDependency).filter(
        BusinessProcessDependency.depends_on_process_id == business_process_id
    ).all()
    
    result = []
    for dep in dependencies:
        bp = db.query(BusinessProcess).filter(BusinessProcess.id == dep.business_process_id).first()
        result.append({
            "id": str(dep.id),
            "depends_on_process_id": str(dep.business_process_id),
            "depends_on_process": {
                "id": str(bp.id) if bp else None,
                "name": bp.name if bp else "Unknown",
                "status": bp.status if bp else None,
            } if bp else None,
            "dependency_type": dep.dependency_type,
            "description": dep.description,
            "created_at": dep.created_at.isoformat() if dep.created_at else None,
        })
        # Recursively get downstream
        if bp:
            result.extend(get_downstream_dependents(db, bp.id, visited))
    
    return result


def build_dependency_tree(db: Session, business_process_id: UUID) -> dict:
    """Build a tree structure of dependencies for a business process."""
    upstream = get_upstream_dependencies(db, business_process_id)
    downstream = get_downstream_dependents(db, business_process_id)
    
    return {
        "upstream": upstream,
        "downstream": downstream,
    }