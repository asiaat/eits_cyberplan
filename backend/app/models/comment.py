"""Comment model."""
import uuid

from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class Comment(Base):
    __tablename__ = "comments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    entity_type = Column(String(50), nullable=False)
    entity_id = Column(UUID(as_uuid=True), nullable=False)
    author_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    body = Column(Text, nullable=False)
    created_at = Column(DateTime, server_default="now()")

    tenant = relationship("Tenant", back_populates="comments")
    author_user = relationship("User", back_populates="comments")