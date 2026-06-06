"""Object-Module Mapping model."""
import uuid

from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class ObjectModuleMapping(Base):
    __tablename__ = "object_module_mappings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("app_tenants.id"), nullable=False, index=True)
    target_type = Column(String(50), nullable=False)
    target_id = Column(UUID(as_uuid=True), nullable=False)
    module_id = Column(UUID(as_uuid=True), ForeignKey("eits_modules.id"), nullable=False)
    applicability = Column(String(50), default="pending")
    rationale = Column(Text)
    selected_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    selected_at = Column(DateTime, server_default="now()")

    module = relationship("EitsModule", back_populates="mappings")
    selected_by_user = relationship("User", back_populates="mappings")