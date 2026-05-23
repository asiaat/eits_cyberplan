"""Asset Relation model."""
import uuid

from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class AssetRelation(Base):
    __tablename__ = "asset_relations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    source_asset_id = Column(UUID(as_uuid=True), ForeignKey("assets.id"), nullable=False)
    target_asset_id = Column(UUID(as_uuid=True), ForeignKey("assets.id"), nullable=False)
    relation_type = Column(String(50), nullable=False)  # Legacy - use relation_type_code
    relation_type_code = Column(String(50), ForeignKey("asset_relation_types.code"), nullable=True)
    description = Column(Text)
    bidirectional = Column(Boolean, default=False)
    strength = Column(String(20), default="weak")  # 'strong' or 'weak'
    created_at = Column(DateTime, server_default="now()")

    tenant = relationship("Tenant", back_populates="asset_relations")
    source_asset = relationship("Asset", back_populates="relations_from", foreign_keys=[source_asset_id])
    target_asset = relationship("Asset", back_populates="relations_to", foreign_keys=[target_asset_id])
    relation_type_info = relationship("AssetRelationType", foreign_keys=[relation_type_code])