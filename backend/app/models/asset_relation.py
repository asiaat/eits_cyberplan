"""Asset Relation model."""
import uuid

from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class AssetRelation(Base):
    __tablename__ = "asset_relations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    source_asset_id = Column(UUID(as_uuid=True), ForeignKey("assets.id"), nullable=False)
    target_asset_id = Column(UUID(as_uuid=True), ForeignKey("assets.id"), nullable=False)
    relation_type = Column(String(50), nullable=False)
    description = Column(Text)

    tenant = relationship("Tenant", back_populates="asset_relations")
    source_asset = relationship("Asset", back_populates="relations_from", foreign_keys=[source_asset_id])
    target_asset = relationship("Asset", back_populates="relations_to", foreign_keys=[target_asset_id])