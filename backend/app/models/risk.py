"""Risk model."""
import uuid

from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base, SoftDeleteMixin


class Risk(SoftDeleteMixin, Base):
    __tablename__ = "risks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("app_tenants.id"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    scenario = Column(Text)
    target_type = Column(String(50))
    target_id = Column(UUID(as_uuid=True))
    threat = Column(Text)
    vulnerability = Column(Text)
    likelihood = Column(String(20))
    impact = Column(String(20))
    risk_level = Column(String(20))
    treatment = Column(String(50))
    owner_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    status = Column(String(50), default="identified")
    review_date = Column(DateTime)
    created_at = Column(DateTime, server_default="now()")
    updated_at = Column(DateTime, server_default="now()", onupdate="now()")

    owner_user = relationship("User", back_populates="owned_risks")