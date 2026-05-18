"""AssetModuleMapping model - E-ITS modelleerimine."""
import uuid

from sqlalchemy import Column, String, Text, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class AssetModuleMapping(Base):
    __tablename__ = "asset_module_mappings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("app_tenants.id", ondelete="CASCADE"), nullable=False)
    asset_id = Column(UUID(as_uuid=True), ForeignKey("assets.id", ondelete="CASCADE"), nullable=False)
    module_id = Column(UUID(as_uuid=True), ForeignKey("eits_modules.id", ondelete="CASCADE"), nullable=False)
    justification = Column(Text, nullable=True)
    modeled_by = Column(UUID(as_uuid=True), ForeignKey("local_users.id", ondelete="SET NULL"), nullable=True)
    modeled_at = Column(DateTime(timezone=True), server_default="now()")

    tenant = relationship("AppTenant")
    asset = relationship("Asset")
    module = relationship("EitsModule")
    modeled_by_user = relationship("LocalUser", foreign_keys=[modeled_by])
    imr_items = relationship("ImrItem", back_populates="asset_module_mapping")

    __table_args__ = (
        UniqueConstraint('tenant_id', 'asset_id', 'module_id', name='uq_asset_module_mapping'),
    )