"""Tenant model."""
import uuid
from decimal import Decimal

from sqlalchemy import Column, String, DateTime, Text, JSON, Numeric, Date, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class Tenant(Base):
    __tablename__ = "tenants"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    registry_code = Column(String(20), unique=True, nullable=True)
    legal_form = Column(String(50), nullable=True)
    registration_date = Column(Date, nullable=True)
    status = Column(String(50), nullable=True)
    registered_address = Column(Text, nullable=True)
    contact_address = Column(Text, nullable=True)
    phone = Column(String(50), nullable=True)
    email = Column(String(255), nullable=True)
    website = Column(String(255), nullable=True)
    share_capital = Column(Numeric(15, 2), nullable=True)
    nace_codes = Column(JSON, nullable=True)
    company_type = Column(String(20), nullable=True)
    parent_company_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=True)
    divisions = Column(JSON, default=list)
    created_at = Column(DateTime, server_default="now()")
    updated_at = Column(DateTime, server_default="now()", onupdate="now()")

    users = relationship("Membership", back_populates="tenant")
    business_processes = relationship("BusinessProcess", back_populates="tenant")
    assets = relationship("Asset", back_populates="tenant")
    asset_relations = relationship("AssetRelation", back_populates="tenant")
    process_assets = relationship("ProcessAsset", back_populates="tenant")
    mappings = relationship("ObjectModuleMapping", back_populates="tenant")
    implementation_plan_items = relationship("ImplementationPlanItem", back_populates="tenant")
    risks = relationship("Risk", back_populates="tenant")
    evidences = relationship("Evidence", back_populates="tenant")
    evidence_links = relationship("EvidenceLink", back_populates="tenant")
    audit_logs = relationship("AuditLog", back_populates="tenant")
    comments = relationship("Comment", back_populates="tenant")
    child_tenants = relationship("Tenant", backref="parent", remote_side=[id])