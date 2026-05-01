"""E-ITS Measure model."""
import uuid

from sqlalchemy import Column, String, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class EitsMeasure(Base):
    __tablename__ = "eits_measures"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    catalog_version_id = Column(UUID(as_uuid=True), ForeignKey("eits_catalog_versions.id"), nullable=False)
    code = Column(String(50), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    measure_level = Column(String(50))
    responsible_role = Column(String(100))
    implementation_guidance = Column(Text)

    catalog_version = relationship("EitsCatalogVersion", back_populates="measures")
    modules = relationship("EitsModuleMeasure", back_populates="measure")
    implementation_items = relationship("ImplementationPlanItem", back_populates="measure")