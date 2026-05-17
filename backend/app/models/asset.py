"""Asset model."""
import uuid

from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class Asset(Base):
    __tablename__ = "assets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
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
    created_at = Column(DateTime, server_default="now()")
    updated_at = Column(DateTime, server_default="now()", onupdate="now()")

    tenant = relationship("Tenant", back_populates="assets")
    owner_user = relationship("User", back_populates="owned_assets", foreign_keys=[owner_user_id])
    person = relationship("Person", back_populates="assets")
    relations_from = relationship("AssetRelation", back_populates="source_asset", foreign_keys="AssetRelation.source_asset_id")
    relations_to = relationship("AssetRelation", back_populates="target_asset", foreign_keys="AssetRelation.target_asset_id")
    processes = relationship("ProcessAsset", back_populates="asset")