import uuid

from sqlalchemy import Column, String, Text, DateTime, Boolean, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class ImrSnapshot(Base):
    __tablename__ = "imr_snapshots"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("app_tenants.id", ondelete="CASCADE"), nullable=False)
    protection_mode_selection_id = Column(UUID(as_uuid=True), ForeignKey("protectionmode_selections.id", ondelete="SET NULL"), nullable=True)
    label = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    is_current = Column(Boolean, nullable=False, default=False)
    item_count = Column(Integer, nullable=False, default=0)
    created_by = Column(UUID(as_uuid=True), ForeignKey("local_users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default="now()")
    restored_from = Column(UUID(as_uuid=True), nullable=True)

    tenant = relationship("AppTenant")
    protection_mode_selection = relationship("ProtectionModeSelection")
    creator = relationship("LocalUser", foreign_keys=[created_by])
    imr_items = relationship("ImrItem", back_populates="imr_snapshot")
