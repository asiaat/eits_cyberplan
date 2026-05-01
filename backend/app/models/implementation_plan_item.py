"""Implementation Plan Item (IMR) model."""
import uuid

from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class ImplementationPlanItem(Base):
    __tablename__ = "implementation_plan_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    measure_id = Column(UUID(as_uuid=True), ForeignKey("eits_measures.id"), nullable=False)
    target_type = Column(String(50), nullable=False)
    target_id = Column(UUID(as_uuid=True), nullable=False)
    owner_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    status = Column(String(50), default="not_started")
    priority = Column(String(20), default="medium")
    due_date = Column(DateTime)
    implementation_comment = Column(Text)
    verification_method = Column(Text)
    accepted_risk_id = Column(UUID(as_uuid=True))
    created_at = Column(DateTime, server_default="now()")
    updated_at = Column(DateTime, server_default="now()", onupdate="now()")

    tenant = relationship("Tenant", back_populates="implementation_plan_items")
    measure = relationship("EitsMeasure", back_populates="implementation_items")
    owner_user = relationship("User", back_populates="owned_implementation_items")