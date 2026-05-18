"""E-ITS Module model - extends existing eits_modules table."""
import uuid

from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class EitsModule(Base):
    __tablename__ = "eits_modules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    catalog_version_id = Column(UUID(as_uuid=True), ForeignKey("eits_catalog_versions.id"), nullable=False)
    code = Column(String(50), nullable=False)
    name = Column(String(255), nullable=False)
    module_group = Column(String(10), nullable=True)
    category = Column(String(100), nullable=True)
    description = Column(Text)
    module_type = Column(String(50), nullable=True)
    source_url = Column(String(500), nullable=True)

    catalog_version = relationship("EitsCatalogVersion", back_populates="modules")
    measures = relationship("EitsModuleMeasure", back_populates="module")
    mappings = relationship("ObjectModuleMapping", back_populates="module")
    catalog_measures = relationship("EitsCatalogMeasure", back_populates="module")
    module_threats = relationship("ModuleThreat", back_populates="module")
    process_module_assignments = relationship("ProcessModuleAssignment", back_populates="module")

    @property
    def is_process_module(self):
        return self.module_type == "PROCESS" or self.module_group in ("ISMS", "ORP", "CON", "OPS", "DER")

    @property
    def is_system_module(self):
        return self.module_type == "SYSTEM" or self.module_group in ("INF", "NET", "SYS", "APP", "IND")