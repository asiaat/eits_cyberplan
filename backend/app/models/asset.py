"""Asset model."""
import uuid

from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Boolean, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base, SoftDeleteMixin


class Asset(SoftDeleteMixin, Base):
    __tablename__ = "assets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("app_tenants.id"), nullable=False, index=True)
    owner_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    person_id = Column(UUID(as_uuid=True), ForeignKey("persons.id"), nullable=True, index=True)
    name = Column(String(255), nullable=False)
    asset_type = Column(String(50), nullable=False)
    description = Column(Text)
    remarks = Column(Text)
    criticality = Column(String(20), default="normal")
    confidentiality_need = Column(String(20), default="normal")
    integrity_need = Column(String(20), default="normal")
    availability_need = Column(String(20), default="normal")
    lifecycle_status = Column(String(50), default="active")
    is_grouped = Column(Boolean, default=False, server_default='false', nullable=False)
    quantity = Column(Integer, default=1, server_default='1', nullable=False)
    group_name = Column(String(255), nullable=True)
    is_core = Column(Boolean, default=False, server_default='false', nullable=False)
    created_at = Column(DateTime, server_default="now()")
    updated_at = Column(DateTime, server_default="now()", onupdate="now()")

    owner_user = relationship("User", back_populates="owned_assets", foreign_keys=[owner_user_id])
    person = relationship("Person", back_populates="assets")
    relations_from = relationship("AssetRelation", back_populates="source_asset", foreign_keys="AssetRelation.source_asset_id")
    relations_to = relationship("AssetRelation", back_populates="target_asset", foreign_keys="AssetRelation.target_asset_id")
    processes = relationship("ProcessAsset", back_populates="asset")
    module_mappings = relationship("AssetModuleMapping", back_populates="asset", cascade="all, delete-orphan")