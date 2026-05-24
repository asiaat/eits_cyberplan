"""Business Process model."""
import uuid

from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base, SoftDeleteMixin


class BusinessProcess(SoftDeleteMixin, Base):
    __tablename__ = "business_processes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("app_tenants.id"), nullable=False, index=True)
    owner_user_id = Column(UUID(as_uuid=True), ForeignKey("local_users.id"))
    division_id = Column(UUID(as_uuid=True), nullable=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    purpose = Column(Text)
    inputs = Column(Text)
    outputs = Column(Text)
    status = Column(String(50), default="active")
    confidentiality_need = Column(String(20), default="normal")
    integrity_need = Column(String(20), default="normal")
    availability_need = Column(String(20), default="normal")
    created_at = Column(DateTime, server_default="now()")
    updated_at = Column(DateTime, server_default="now()", onupdate="now()")

    tenant = relationship("AppTenant", back_populates="business_processes")
    owner_user = relationship("LocalUser", back_populates="owned_business_processes", foreign_keys=[owner_user_id])
    assets = relationship("ProcessAsset", back_populates="business_process")