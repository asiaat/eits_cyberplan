"""Alert API endpoints."""
from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import DB, CurrentUser, get_current_user
from app.models.alert import Alert
from app.models.membership import Membership

router = APIRouter()


class AlertCreate(BaseModel):
    title: str
    message: Optional[str] = None
    level: str = "info"
    target_role: str = "all"
    link: Optional[str] = None


class AlertResponse(BaseModel):
    id: str
    title: str
    message: Optional[str]
    level: str
    target_role: str
    is_read: str
    read_at: Optional[datetime]
    created_at: datetime
    link: Optional[str]
    is_active: str

    model_config = {"from_attributes": True}


def get_user_role_codes(db: Session, user_id: str) -> List[str]:
    """Get list of role codes for a user."""
    memberships = db.query(Membership).filter(Membership.user_id == user_id).all()
    role_codes = []
    for m in memberships:
        if m.role:
            role_codes.append(m.role.code)
    return role_codes


@router.get("/", response_model=List[AlertResponse])
def list_alerts(
    db: DB,
    current_user: CurrentUser,
    unread_only: bool = False,
    include_inactive: bool = False,
):
    """List alerts for current user based on their role."""
    user_roles = get_user_role_codes(db, current_user.id)
    
    query = db.query(Alert).filter(
        (Alert.target_role == "all") |
        (Alert.target_role.in_(user_roles))
    )
    
    # Filter out inactive alerts by default
    if not include_inactive:
        query = query.filter(Alert.is_active == "true")
    
    if unread_only:
        query = query.filter(Alert.is_read == "false")
    
    alerts = query.order_by(Alert.created_at.desc()).all()
    
    return [
        AlertResponse(
            id=str(a.id),
            title=a.title,
            message=a.message,
            level=a.level,
            target_role=a.target_role,
            is_read=a.is_read,
            read_at=a.read_at,
            created_at=a.created_at,
            link=a.link,
            is_active=a.is_active,
        )
        for a in alerts
    ]


@router.get("/history", response_model=List[AlertResponse])
def list_alert_history(
    db: DB,
    current_user: CurrentUser,
):
    """List archived/inactive alerts (admin only)."""
    from app.core.permissions import has_permission
    
    if not has_permission(db, current_user, "users.view"):
        raise HTTPException(status_code=403, detail="Only admins can view alert history")
    
    user_roles = get_user_role_codes(db, current_user.id)
    
    alerts = db.query(Alert).filter(
        (Alert.target_role == "all") |
        (Alert.target_role.in_(user_roles)),
        Alert.is_active == "false"
    ).order_by(Alert.created_at.desc()).all()
    
    return [
        AlertResponse(
            id=str(a.id),
            title=a.title,
            message=a.message,
            level=a.level,
            target_role=a.target_role,
            is_read=a.is_read,
            read_at=a.read_at,
            created_at=a.created_at,
            link=a.link,
            is_active=a.is_active,
        )
        for a in alerts
    ]


@router.post("/", response_model=AlertResponse)
def create_alert(
    alert_in: AlertCreate,
    db: DB,
    current_user: CurrentUser,
):
    """Create a new alert (admin only)."""
    from app.core.permissions import has_permission
    
    if not has_permission(db, current_user, "users.create"):
        raise HTTPException(status_code=403, detail="Only admins can create alerts")
    
    alert = Alert(
        title=alert_in.title,
        message=alert_in.message,
        level=alert_in.level,
        target_role=alert_in.target_role,
        link=alert_in.link,
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)
    
    return AlertResponse(
        id=str(alert.id),
        title=alert.title,
        message=alert.message,
        level=alert.level,
        target_role=alert.target_role,
        is_read=alert.is_read,
        read_at=alert.read_at,
        created_at=alert.created_at,
        link=alert.link,
        is_active=alert.is_active,
    )


@router.patch("/{alert_id}/read", response_model=AlertResponse)
def mark_alert_read(
    alert_id: str,
    db: DB,
    current_user: CurrentUser,
):
    """Mark an alert as read."""
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    alert.is_read = "true"
    alert.read_at = datetime.utcnow()
    db.commit()
    db.refresh(alert)
    
    return AlertResponse(
        id=str(alert.id),
        title=alert.title,
        message=alert.message,
        level=alert.level,
        target_role=alert.target_role,
        is_read=alert.is_read,
        read_at=alert.read_at,
        created_at=alert.created_at,
        link=alert.link,
        is_active=alert.is_active,
    )


@router.delete("/{alert_id}")
def delete_alert(
    alert_id: str,
    db: DB,
    current_user: CurrentUser,
):
    """Delete/dismiss an alert."""
    from app.core.permissions import has_permission
    
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    # Anyone who can see the alert can dismiss it
    user_roles = get_user_role_codes(db, current_user.id)
    if alert.target_role != "all" and alert.target_role not in user_roles:
        raise HTTPException(status_code=403, detail="Cannot delete this alert")
    
    db.delete(alert)
    db.commit()
    
    return {"message": "Alert deleted"}


@router.post("/bulk-read")
def mark_all_alerts_read(
    db: DB,
    current_user: CurrentUser,
):
    """Mark all visible alerts as read."""
    user_roles = get_user_role_codes(db, current_user.id)
    
    db.query(Alert).filter(
        ((Alert.target_role == "all") | (Alert.target_role.in_(user_roles))),
        (Alert.is_read == "false")
    ).update({
        "is_read": "true",
        "read_at": datetime.utcnow()
    })
    db.commit()
    
    return {"message": "All alerts marked as read"}