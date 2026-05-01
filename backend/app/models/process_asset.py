"""Process-Asset relation model."""
import uuid

from sqlalchemy import Column, String, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class ProcessAsset(Base):
    __tablename__ = "process_assets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    business_process_id = Column(UUID(as_uuid=True), ForeignKey("business_processes.id"), nullable=False)
    asset_id = Column(UUID(as_uuid=True), ForeignKey("assets.id"), nullable=False)
    relation_description = Column(Text)

    tenant = relationship("Tenant", back_populates="process_assets")
    business_process = relationship("BusinessProcess", back_populates="assets")
    asset = relationship("Asset", back_populates="processes")