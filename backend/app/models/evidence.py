"""Evidence model."""
import uuid

from sqlalchemy import Column, String, Text, DateTime, ForeignKey, BigInteger, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base, SoftDeleteMixin


class Evidence(SoftDeleteMixin, Base):
    __tablename__ = "evidences"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("app_tenants.id"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    evidence_type = Column(String(50), nullable=False)
    storage_uri = Column(String(500))
    external_url = Column(String(500))
    file_hash = Column(String(64), nullable=True, index=True)
    version = Column(String(20))
    owner_user_id = Column(UUID(as_uuid=True), ForeignKey("local_users.id"))
    valid_from = Column(DateTime)
    valid_until = Column(DateTime)
    review_due_date = Column(DateTime)
    file_size = Column(BigInteger, nullable=True)
    mime_type = Column(String(100), nullable=True)
    download_count = Column(Integer, default=0)
    created_at = Column(DateTime, server_default="now()")

    owner_user = relationship("LocalUser", back_populates="owned_evidences")
    links = relationship("EvidenceLink", back_populates="evidence")