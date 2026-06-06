"""Person model."""
import uuid

from sqlalchemy import Column, String, Text, DateTime, Date, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base, SoftDeleteMixin


class Person(SoftDeleteMixin, Base):
    __tablename__ = "persons"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    national_id = Column(String(50), nullable=True, unique=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    date_of_birth = Column(Date, nullable=True)
    email = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    additional_info = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default="now()")
    updated_at = Column(DateTime, server_default="now()", onupdate="now()")

    organizations = relationship("PersonOrganization", back_populates="person")
    assets = relationship("Asset", back_populates="person")

    @property
    def name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip()


class PersonOrganization(Base):
    __tablename__ = "person_organizations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    person_id = Column(UUID(as_uuid=True), ForeignKey("persons.id"), nullable=False, index=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("app_tenants.id"), nullable=False, index=True)
    role = Column(String(100), nullable=True)
    created_at = Column(DateTime, server_default="now()")

    person = relationship("Person", back_populates="organizations")