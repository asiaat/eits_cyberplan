"""DamageAssessment model - kaitsetarbe määramine."""
import uuid

from sqlalchemy import Column, Integer, Text, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base, SoftDeleteMixin


class DamageAssessment(SoftDeleteMixin, Base):
    __tablename__ = "damage_assessments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("app_tenants.id", ondelete="CASCADE"), nullable=False)
    business_process_id = Column(UUID(as_uuid=True), ForeignKey("business_processes.id", ondelete="CASCADE"), nullable=False)
    damage_scenario_id = Column(UUID(as_uuid=True), ForeignKey("damage_scenarios.id"), nullable=False)
    availability_impact = Column(Integer, default=0)
    confidentiality_impact = Column(Integer, default=0)
    integrity_impact = Column(Integer, default=0)
    damage_category = Column(Integer, nullable=True)
    justification = Column(Text, nullable=True)
    assessed_by = Column(UUID(as_uuid=True), ForeignKey("local_users.id", ondelete="SET NULL"), nullable=True)
    assessed_at = Column(DateTime(timezone=True), server_default="now()")

    tenant = relationship("AppTenant")
    business_process = relationship("BusinessProcess")
    damage_scenario = relationship("DamageScenario")
    assessed_by_user = relationship("LocalUser", foreign_keys=[assessed_by])

    __table_args__ = (
        UniqueConstraint('tenant_id', 'business_process_id', 'damage_scenario_id', name='uq_damage_assessment'),
    )