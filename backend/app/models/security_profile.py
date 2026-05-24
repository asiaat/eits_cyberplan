"""SecurityProfile model - protection mode selection."""
import uuid

from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base, SoftDeleteMixin


class SecurityProfile(SoftDeleteMixin, Base):
    __tablename__ = "security_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("app_tenants.id", ondelete="CASCADE"), nullable=False)
    catalog_version_id = Column(UUID(as_uuid=True), ForeignKey("eits_catalog_versions.id", ondelete="SET NULL"), nullable=True)
    security_approach = Column(String(20), nullable=False, default="BASIC")
    approved_by = Column(UUID(as_uuid=True), ForeignKey("local_users.id", ondelete="SET NULL"), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default="now()")
    updated_at = Column(DateTime(timezone=True), server_default="now()", onupdate="now()")

    tenant = relationship("AppTenant", back_populates="security_profiles")
    catalog_version = relationship("EitsCatalogVersion", back_populates="security_profiles")
    approved_by_user = relationship("LocalUser", foreign_keys=[approved_by])

    @property
    def approach_display(self):
        return {
            "BASIC": "Põhiturve",
            "STANDARD": "Standardturve",
            "CORE": "Tuumikuturve",
        }.get(self.security_approach, self.security_approach)