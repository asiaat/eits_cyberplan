from datetime import datetime
from typing import Any, Optional

from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog


def log_audit(
    db: Session,
    tenant_id: str,
    actor_user_id: str,
    action: str,
    entity_type: str,
    entity_id: str,
    before_json: Optional[dict] = None,
    after_json: Optional[dict] = None,
) -> AuditLog:
    entry = AuditLog(
        tenant_id=tenant_id,
        actor_user_id=actor_user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        before_json=before_json,
        after_json=after_json,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def get_audit_trail(
    db: Session,
    tenant_id: str,
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None,
    limit: int = 100,
) -> list[AuditLog]:
    query = db.query(AuditLog).filter(AuditLog.tenant_id == tenant_id)
    if entity_type:
        query = query.filter(AuditLog.entity_type == entity_type)
    if entity_id:
        query = query.filter(AuditLog.entity_id == entity_id)
    return query.order_by(AuditLog.created_at.desc()).limit(limit).all()