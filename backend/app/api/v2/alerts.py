"""Alerts API v2."""
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.api.deps import DB
from app.api.v2.auth import CurrentUserV2

router = APIRouter()


class AlertResponse(BaseModel):
    id: str
    title: str
    message: str | None
    level: str
    target_role: str
    is_read: bool
    read_at: str | None
    created_at: str
    link: str | None
    is_active: bool


@router.get("/", response_model=List[AlertResponse])
def list_alerts(db: DB, current_user = CurrentUserV2):
    """List active alerts for current user."""
    from app.models.alert import Alert
    
    role_filter = current_user.roles[0].role_name if current_user.roles else "all"
    
    alerts = db.query(Alert).filter(
        Alert.is_active == True,
        Alert.target_role.in_(["all", "admin", "ism"]),
    ).order_by(Alert.created_at.desc()).limit(50).all()
    
    return [
        AlertResponse(
            id=str(a.id),
            title=a.title,
            message=a.message,
            level=a.level,
            target_role=a.target_role,
            is_read=a.is_read or False,
            read_at=a.read_at,
            created_at=str(a.created_at),
            link=a.link,
            is_active=a.is_active or False
        )
        for a in alerts
    ]


@router.get("/history", response_model=List[AlertResponse])
def list_alert_history(db: DB, current_user = CurrentUserV2):
    """List alert history for current user."""
    from app.models.alert import Alert
    
    alerts = db.query(Alert).order_by(Alert.created_at.desc()).limit(100).all()
    
    return [
        AlertResponse(
            id=str(a.id),
            title=a.title,
            message=a.message,
            level=a.level,
            target_role=a.target_role,
            is_read=a.is_read or False,
            read_at=a.read_at,
            created_at=str(a.created_at),
            link=a.link,
            is_active=a.is_active or False
        )
        for a in alerts
    ]


@router.post("/{alert_id}/read")
def mark_alert_read(alert_id: UUID, db: DB, current_user = CurrentUserV2):
    """Mark alert as read."""
    from app.models.alert import Alert
    
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    alert.is_read = True
    db.commit()
    
    return {"message": "Alert marked as read"}


@router.post("/read-all")
def mark_all_alerts_read(db: DB, current_user = CurrentUserV2):
    """Mark all alerts as read."""
    from app.models.alert import Alert
    
    db.query(Alert).filter(Alert.is_active == True).update({"is_read": True})
    db.commit()
    
    return {"message": "All alerts marked as read"}


@router.delete("/{alert_id}")
def dismiss_alert(alert_id: UUID, db: DB, current_user = CurrentUserV2):
    """Dismiss an alert."""
    from app.models.alert import Alert
    
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    alert.is_active = False
    db.commit()
    
    return {"message": "Alert dismissed"}