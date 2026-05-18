"""E-ITS Threat model and ModuleThreat association."""
import uuid

from sqlalchemy import Column, String, Text, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class EitsThreat(Base):
    __tablename__ = "eits_threats"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    version_id = Column(UUID(as_uuid=True), ForeignKey("eits_catalog_versions.id", ondelete="CASCADE"), nullable=False)
    code = Column(String(30), nullable=False)
    category = Column(String(100), nullable=True)
    impact_area = Column(String(100), nullable=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    version = relationship("EitsCatalogVersion", back_populates="threats")
    module_threats = relationship("ModuleThreat", back_populates="threat")


class ModuleThreat(Base):
    __tablename__ = "module_threats"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    module_id = Column(UUID(as_uuid=True), ForeignKey("eits_modules.id", ondelete="CASCADE"), nullable=False)
    threat_id = Column(UUID(as_uuid=True), ForeignKey("eits_threats.id", ondelete="CASCADE"), nullable=False)
    relevance_note = Column(Text, nullable=True)

    module = relationship("EitsModule", back_populates="module_threats")
    threat = relationship("EitsThreat", back_populates="module_threats")