"""TurbeviisSelection model - turbeviisi valik koos tõendiga."""
import uuid

from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class TurbeviisSelection(Base):
    __tablename__ = "turbeviis_selections"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("app_tenants.id", ondelete="CASCADE"), nullable=False)
    catalog_version_id = Column(UUID(as_uuid=True), ForeignKey("eits_catalog_versions.id", ondelete="SET NULL"), nullable=True)
    security_approach = Column(String(20), nullable=False, default="BASIC")
    evidence_id = Column(UUID(as_uuid=True), ForeignKey("evidences.id", ondelete="SET NULL"), nullable=True)
    approved_by = Column(UUID(as_uuid=True), ForeignKey("local_users.id", ondelete="SET NULL"), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    notes = Column(Text, nullable=True)
    is_active = Column(Boolean(), nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default="now()")
    updated_at = Column(DateTime(timezone=True), server_default="now()", onupdate="now()")

    tenant = relationship("AppTenant", back_populates="turbeviis_selections")
    catalog_version = relationship("EitsCatalogVersion", back_populates="turbeviis_selections")
    evidence = relationship("Evidence")
    approved_by_user = relationship("LocalUser", foreign_keys=[approved_by])