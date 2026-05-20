"""BusinessProcessDependency model - tracks process-to-process dependencies."""
import uuid

from sqlalchemy import Column, String, Text, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class BusinessProcessDependency(Base):
    __tablename__ = "business_process_dependencies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("app_tenants.id", ondelete="CASCADE"), nullable=False)
    primary_process_id = Column(UUID(as_uuid=True), ForeignKey("business_processes.id", ondelete="CASCADE"), nullable=False)
    depends_on_process_id = Column(UUID(as_uuid=True), ForeignKey("business_processes.id", ondelete="CASCADE"), nullable=False)
    dependency_type = Column(String(50), nullable=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default="now()")

    tenant = relationship("AppTenant")
    primary_process = relationship("BusinessProcess", foreign_keys=[primary_process_id])
    depends_on_process = relationship("BusinessProcess", foreign_keys=[depends_on_process_id])

    __table_args__ = (
        UniqueConstraint('primary_process_id', 'depends_on_process_id', name='uq_bp_dependency_pair'),
    )