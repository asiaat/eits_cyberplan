"""Alert model for notifications."""
import uuid
from datetime import datetime

from sqlalchemy import Column, String, Text, DateTime, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=True)
    level = Column(Enum('info', 'warning', 'error', 'success', name='alert_level'), nullable=False, default='info')
    target_role = Column(Enum('admin', 'ism', 'all', name='alert_target_role'), nullable=False, default='all')
    is_read = Column(String(10), nullable=False, default="false")
    read_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default="now()")
    link = Column(String(255), nullable=True)
    is_active = Column(String(10), nullable=False, default="true")
    tenant_id = Column(UUID(as_uuid=True), nullable=True)