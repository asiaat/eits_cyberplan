"""ProtectionNeedSummary model - koond-kaitsetarve."""
import uuid

from sqlalchemy import Column, String, Text, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class ProtectionNeedSummary(Base):
    __tablename__ = "protection_need_summaries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("app_tenants.id", ondelete="CASCADE"), nullable=False)
    business_process_id = Column(UUID(as_uuid=True), ForeignKey("business_processes.id", ondelete="CASCADE"), nullable=False)
    protection_need = Column(String(20), nullable=False, default="NORMAL")
    confidentiality_need = Column(String(20), default="NORMAL")
    integrity_need = Column(String(20), default="NORMAL")
    availability_need = Column(String(20), default="NORMAL")
    justification = Column(Text, nullable=True)
    approved_by = Column(UUID(as_uuid=True), ForeignKey("local_users.id", ondelete="SET NULL"), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default="now()")
    updated_at = Column(DateTime(timezone=True), server_default="now()", onupdate="now()")

    tenant = relationship("AppTenant")
    business_process = relationship("BusinessProcess")
    approved_by_user = relationship("LocalUser", foreign_keys=[approved_by])

    __table_args__ = (
        UniqueConstraint('tenant_id', 'business_process_id', name='uq_protection_need_summary'),
    )

    @staticmethod
    def level_from_damage(damage_category: int) -> str:
        if damage_category <= 1:
            return "NORMAL"
        elif damage_category == 2:
            return "HIGH"
        else:
            return "VERY_HIGH"