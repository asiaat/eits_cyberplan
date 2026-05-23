"""Asset Relation Type model."""
import uuid

from sqlalchemy import Column, String, Text, DateTime, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class AssetRelationType(Base):
    __tablename__ = "asset_relation_types"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code = Column(String(50), nullable=False, unique=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    source_types = Column(String(500))  # JSON array
    target_types = Column(String(500))  # JSON array
    bidirectional = Column(Boolean, default=False)
    strength = Column(String(20), default="weak")  # 'strong' or 'weak'
    created_at = Column(DateTime, server_default="now()")

    relations = relationship("AssetRelation", foreign_keys="AssetRelation.relation_type_code", back_populates="relation_type_info")