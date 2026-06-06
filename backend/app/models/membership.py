"""Membership model (tenant-user-role junction)."""
import uuid

from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class Membership(Base):
    __tablename__ = "memberships"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("app_tenants.id"), nullable=True)  # nullable for backward compat
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    role_id = Column(String(50), ForeignKey("roles.id"), nullable=False)

    # For new tier system
    local_user_id = Column(UUID(as_uuid=True), ForeignKey("local_users.id"), nullable=True)

    user = relationship("User", back_populates="memberships")
    role = relationship("Role", back_populates="memberships")
    local_user = relationship("LocalUser", back_populates="memberships")