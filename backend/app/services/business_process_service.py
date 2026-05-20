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


def get_ism_admin_roles(db: Session, tenant_id: UUID) -> list[str]:
    """Get list of role names that count as ISM or admin for approval."""
    roles = db.query(EITSRole).filter(EITSRole.tenant_id == tenant_id).all()
    ism_admin_roles = []
    for role in roles:
        if role.role_name.lower() in ("infoturbejuht", "ism", "admin", "juhtkond"):
            ism_admin_roles.append(role.role_name)
    return ism_admin_roles


def get_user_roles(db: Session, user_id: UUID) -> list[str]:
    """Get role names for a given user."""
    user_roles = db.query(UserRole).filter(UserRole.user_id == user_id).all()
    role_ids = [ur.role_id for ur in user_roles]
    if not role_ids:
        return []
    roles = db.query(EITSRole).filter(EITSRole.id.in_(role_ids)).all()
    return [r.role_name for r in roles]


def user_has_approval_role(db: Session, user_id: UUID, tenant_id: UUID) -> bool:
    """Check if user has admin or ISM role for approving high protection needs."""
    user_roles = get_user_roles(db, user_id)
    ism_admin_roles = get_ism_admin_roles(db, tenant_id)
    return any(role in ism_admin_roles for role in user_roles)


def validate_protection_need_justification(
    db: Session,
    tenant_id: UUID,
    protection_need: str,
    justification: Optional[str],
    approved_by: Optional[UUID],
) -> tuple[bool, str]:
    """SOP 2: Validate justification and approval for HIGH/VERY_HIGH protection needs.

    Returns (is_valid, error_message).
    """
    if not is_high_or_very_high(protection_need):
        return True, ""

    if not justification or len(justification.strip()) < 20:
        return False, "Justification must be at least 20 characters for HIGH or VERY_HIGH protection needs"

    if not approved_by:
        return False, "Approval from admin or ISM role is required for HIGH or VERY_HIGH protection needs"

    if not user_has_approval_role(db, approved_by, tenant_id):
        return False, "Approved_by must be a user with admin or ISM role"

    return True, ""


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

    When a business process protection need is set or upgraded to HIGH or VERY_HIGH,
    all supporting assets linked to it must have their threat profiles reviewed.
    """
    asset_count = len(asset_ids)
    message = (
        f"Business process '{business_process_name}' has {protection_need.upper()} protection need. "
        f"Review required for {asset_count} linked asset(s) baseline security level against "
        f"standard or high-level E-ITS measures."
    )

    alert = Alert(
        title=f"Asset Security Review Required - {business_process_name}",
        message=message,
        level="warning",
        target_role="ism",
        is_read="false",
        is_active="true",
        tenant_id=tenant_id,
        link=f"/business-processes/{business_process_id}/assets",
    )
    db.add(alert)
    db.flush()
    return alert


def check_circular_dependency(
    db: Session,
    tenant_id: UUID,
    primary_process_id: UUID,
    depends_on_process_id: UUID,
) -> tuple[bool, Optional[str]]:
    """Check if adding a dependency would create a circular reference.

    Uses BFS to traverse the dependency graph from depends_on_process_id
    to see if we can reach primary_process_id (which would mean a cycle).

    Returns (would_create_cycle, error_message).
    """
    if primary_process_id == depends_on_process_id:
        return True, "A process cannot depend on itself"

    visited = set()
    queue = [depends_on_process_id]

    while queue:
        current = queue.pop(0)
        if current == primary_process_id:
            return True, "Adding this dependency would create a circular reference"

        if current in visited:
            continue
        visited.add(current)

        deps = db.query(BusinessProcessDependency).filter(
            BusinessProcessDependency.tenant_id == tenant_id,
            BusinessProcessDependency.primary_process_id == current
        ).all()

        for dep in deps:
            if dep.depends_on_process_id not in visited:
                queue.append(dep.depends_on_process_id)

    return False, ""


def get_upstream_dependencies(
    db: Session,
    tenant_id: UUID,
    process_id: UUID,
) -> list[BusinessProcessDependency]:
    """Get all processes that this process depends on (upstream dependencies)."""
    return db.query(BusinessProcessDependency).filter(
        BusinessProcessDependency.tenant_id == tenant_id,
        BusinessProcessDependency.primary_process_id == process_id
    ).all()


def get_downstream_dependents(
    db: Session,
    tenant_id: UUID,
    process_id: UUID,
) -> list[BusinessProcessDependency]:
    """Get all processes that depend on this process (downstream dependents)."""
    return db.query(BusinessProcessDependency).filter(
        BusinessProcessDependency.tenant_id == tenant_id,
        BusinessProcessDependency.depends_on_process_id == process_id
    ).all()


def build_dependency_tree(
    db: Session,
    tenant_id: UUID,
    process_id: UUID,
) -> dict:
    """Build a tree structure of process dependencies.

    Returns dict with 'upstream' (what this process depends on) and
    'downstream' (what depends on this process) arrays with full BP info.
    """
    upstream = get_upstream_dependencies(db, tenant_id, process_id)
    downstream = get_downstream_dependents(db, tenant_id, process_id)

    upstream_bps = []
    for dep in upstream:
        bp = db.query(BusinessProcess).filter(BusinessProcess.id == dep.depends_on_process_id).first()
        if bp:
            upstream_bps.append({
                "id": str(bp.id),
                "name": bp.name,
                "status": bp.status,
                "dependency_type": dep.dependency_type,
                "description": dep.description,
            })

    downstream_bps = []
    for dep in downstream:
        bp = db.query(BusinessProcess).filter(BusinessProcess.id == dep.primary_process_id).first()
        if bp:
            downstream_bps.append({
                "id": str(bp.id),
                "name": bp.name,
                "status": bp.status,
                "dependency_type": dep.dependency_type,
                "description": dep.description,
            })

    return {
        "upstream": upstream_bps,
        "downstream": downstream_bps,
    }