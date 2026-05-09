"""Division model for organizational units."""
import uuid

from sqlalchemy import Column, String, Text, Boolean, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class Division(Base):
    __tablename__ = "divisions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    parent_division_id = Column(UUID(as_uuid=True), ForeignKey("divisions.id"), nullable=True)
    code = Column(String(50), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    head_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    is_active = Column(String(10), nullable=False, default="true")
    sort_order = Column(Integer, default=0)

    tenant = relationship("Tenant", back_populates="divisions")
    parent = relationship("Division", remote_side=[id], backref="children")
    head_user = relationship("User")
    members = relationship("Membership", back_populates="division")
    business_processes = relationship("BusinessProcess", back_populates="division")