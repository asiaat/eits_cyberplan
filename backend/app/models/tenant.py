"""Tenant model."""
import uuid

from sqlalchemy import Column, String, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class Tenant(Base):
    __tablename__ = "tenants"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    registry_code = Column(String(20), unique=True, nullable=True)
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