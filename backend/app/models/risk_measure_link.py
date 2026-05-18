"""RiskMeasureLink and DamageCategoryThreshold models."""
import uuid

from sqlalchemy import Column, String, Text, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class RiskMeasureLink(Base):
    __tablename__ = "risk_measure_links"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("app_tenants.id", ondelete="CASCADE"), nullable=False)
    risk_id = Column(UUID(as_uuid=True), ForeignKey("risks.id", ondelete="CASCADE"), nullable=False)
    imr_item_id = Column(UUID(as_uuid=True), ForeignKey("imr_items.id", ondelete="SET NULL"), nullable=True)
    measure_id = Column(UUID(as_uuid=True), ForeignKey("eits_catalog_measures.id", ondelete="SET NULL"), nullable=True)
    custom_measure_name = Column(String(255), nullable=True)
    custom_measure_description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default="now()")

    tenant = relationship("AppTenant")
    risk = relationship("Risk")
    imr_item = relationship("ImrItem", back_populates="risk_measure_links")
    measure = relationship("EitsCatalogMeasure", back_populates="risk_measure_links")


class DamageCategoryThreshold(Base):
    __tablename__ = "damage_category_thresholds"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("app_tenants.id", ondelete="CASCADE"), nullable=False)
    damage_scenario_id = Column(UUID(as_uuid=True), ForeignKey("damage_scenarios.id", ondelete="CASCADE"), nullable=False)
    negligible_description = Column(Text, nullable=True)
    limited_description = Column(Text, nullable=True)
    serious_description = Column(Text, nullable=True)
    catastrophic_description = Column(Text, nullable=True)
    approved_by = Column(UUID(as_uuid=True), ForeignKey("local_users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default="now()")
    updated_at = Column(DateTime(timezone=True), server_default="now()", onupdate="now()")

    tenant = relationship("AppTenant")
    damage_scenario = relationship("DamageScenario")
    approved_by_user = relationship("LocalUser", foreign_keys=[approved_by])

    __table_args__ = (
        UniqueConstraint('tenant_id', 'damage_scenario_id', name='uq_damage_threshold'),
    )


class ProcessModuleAssignment(Base):
    __tablename__ = "process_module_assignments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("app_tenants.id", ondelete="CASCADE"), nullable=False)
    module_id = Column(UUID(as_uuid=True), ForeignKey("eits_modules.id", ondelete="CASCADE"), nullable=False)
    is_applicable = Column(String(1), default="1")
    non_applicability_justification = Column(Text, nullable=True)
    assigned_by = Column(UUID(as_uuid=True), ForeignKey("local_users.id", ondelete="SET NULL"), nullable=True)
    assigned_at = Column(DateTime(timezone=True), server_default="now()")

    tenant = relationship("AppTenant")
    module = relationship("EitsModule", back_populates="process_module_assignments")
    assigned_by_user = relationship("LocalUser", foreign_keys=[assigned_by])

    __table_args__ = (
        UniqueConstraint('tenant_id', 'module_id', name='uq_process_module_assignment'),
    )