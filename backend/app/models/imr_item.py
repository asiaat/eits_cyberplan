"""ImrItem model - E-ITS IMR with PEARO status."""
import uuid

from sqlalchemy import Column, String, Text, Date, DateTime, Boolean, ForeignKey, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class ImrItem(Base):
    __tablename__ = "imr_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("app_tenants.id", ondelete="CASCADE"), nullable=False)
    asset_module_mapping_id = Column(UUID(as_uuid=True), ForeignKey("asset_module_mappings.id", ondelete="CASCADE"), nullable=True)
    bp_module_mapping_id = Column(UUID(as_uuid=True), ForeignKey("bp_module_mappings.id", ondelete="CASCADE"), nullable=True)
    measure_id = Column(UUID(as_uuid=True), ForeignKey("eits_catalog_measures.id", ondelete="CASCADE"), nullable=False)
    is_process_module_measure = Column(Boolean, default=False)
    pearo_status = Column(String(1), nullable=False, default="E")
    implementation_description = Column(Text, nullable=True)
    non_implementation_justification = Column(Text, nullable=True)
    partial_scope_description = Column(Text, nullable=True)
    responsible_user_id = Column(UUID(as_uuid=True), ForeignKey("local_users.id", ondelete="SET NULL"), nullable=True)
    due_date = Column(Date, nullable=True)
    next_review_date = Column(Date, nullable=True)
    priority = Column(String(5), default="P2")
    risk_acceptance_approved_by = Column(UUID(as_uuid=True), ForeignKey("local_users.id", ondelete="SET NULL"), nullable=True)
    risk_acceptance_date = Column(DateTime(timezone=True), nullable=True)
    verification_method = Column(Text, nullable=True)
    last_verified_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default="now()")
    updated_at = Column(DateTime(timezone=True), server_default="now()", onupdate="now")
    
    # New fields for enhanced IMR tracking
    mapped_module_id = Column(UUID(as_uuid=True), nullable=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("local_users.id", ondelete="SET NULL"), nullable=True)
    updated_by = Column(UUID(as_uuid=True), ForeignKey("local_users.id", ondelete="SET NULL"), nullable=True)
    status_changed_at = Column(DateTime(timezone=True), nullable=True)
    requirement_profile = Column(String(20), nullable=True)
    todo_description = Column(Text, nullable=True)
    cost_eur = Column(Numeric(12, 2), nullable=True)

    tenant = relationship("AppTenant")
    asset_module_mapping = relationship("AssetModuleMapping", back_populates="imr_items")
    bp_module_mapping = relationship("BusinessProcessModuleMapping", back_populates="imr_items")
    measure = relationship("EitsCatalogMeasure", back_populates="imr_items")
    responsible_user = relationship("LocalUser", foreign_keys=[responsible_user_id])
    risk_acceptance_approver = relationship("LocalUser", foreign_keys=[risk_acceptance_approved_by])
    risk_measure_links = relationship("RiskMeasureLink", back_populates="imr_item")
    creator = relationship("LocalUser", foreign_keys=[created_by])
    modifier = relationship("LocalUser", foreign_keys=[updated_by])

    @property
    def pearo_status_display(self):
        return {
            "U": "Unknown",
            "P": "Not Applicable",
            "E": "Not Implemented",
            "A": "Accepted Risk",
            "R": "Implemented",
            "O": "Partially Implemented",
        }.get(self.pearo_status, self.pearo_status)

    @property
    def priority_display(self):
        return {
            "P1": "First priority",
            "P2": "Next priority",
            "P3": "When possible",
        }.get(self.priority, self.priority)