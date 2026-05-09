"""Membership model (tenant-user-role junction)."""
import uuid

from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class Membership(Base):
    __tablename__ = "memberships"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    role_id = Column(String(50), ForeignKey("roles.id"), nullable=False)
    division_id = Column(UUID(as_uuid=True), ForeignKey("divisions.id"), nullable=True, index=True)

    tenant = relationship("Tenant", back_populates="users")
    user = relationship("User", back_populates="memberships")
    role = relationship("Role", back_populates="memberships")
    division = relationship("Division", back_populates="members")