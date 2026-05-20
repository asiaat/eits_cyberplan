"""E-ITS Catalog Version model."""
import uuid

from sqlalchemy import Boolean, Column, Date, DateTime, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class EitsCatalogVersion(Base):
    __tablename__ = "eits_catalog_versions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    version = Column(String(50), nullable=False)
    source_name = Column(String(255))
    source_file_hash = Column(String(64))
    imported_at = Column(DateTime, server_default="now()")
    active = Column(Boolean, default=False)
    year = Column(String(4), nullable=True)
    name = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=False)
    released_at = Column(Date, nullable=True)

    modules = relationship("EitsModule", back_populates="catalog_version")
    measures = relationship("EitsMeasure", back_populates="catalog_version")
    threats = relationship("EitsThreat", back_populates="version")
    security_profiles = relationship("SecurityProfile", back_populates="catalog_version")
    turbeviis_selections = relationship("TurbeviisSelection", back_populates="catalog_version")
