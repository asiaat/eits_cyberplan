"""E-ITS Module model."""
import uuid

from sqlalchemy import Column, String, Text, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class EitsModule(Base):
    __tablename__ = "eits_modules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    catalog_version_id = Column(UUID(as_uuid=True), ForeignKey("eits_catalog_versions.id"), nullable=False)
    code = Column(String(50), nullable=False)
    name = Column(String(255), nullable=False)
    category = Column(String(100))
    description = Column(Text)
    module_type = Column(String(50))
    source_url = Column(String(500))

    catalog_version = relationship("EitsCatalogVersion", back_populates="modules")
    measures = relationship("EitsModuleMeasure", back_populates="module")
    mappings = relationship("ObjectModuleMapping", back_populates="module")