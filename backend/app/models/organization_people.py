"""Organization People link model."""
import uuid

from sqlalchemy import Column, String, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class OrganizationPeople(Base):
    __tablename__ = "organization_people"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    person_asset_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    created_at = Column(DateTime, server_default="now()")