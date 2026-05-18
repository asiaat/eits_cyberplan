"""E-ITS Catalog Measure model - E-ITS measure with level."""
import uuid

from sqlalchemy import Column, String, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class EitsCatalogMeasure(Base):
    __tablename__ = "eits_catalog_measures"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    module_id = Column(UUID(as_uuid=True), ForeignKey("eits_modules.id", ondelete="CASCADE"), nullable=False)
    code = Column(String(30), nullable=False)
    name = Column(String(255), nullable=False)
    measure_level = Column(String(10), nullable=False)
    description = Column(Text, nullable=True)
    responsible_role = Column(String(100), nullable=True)

    module = relationship("EitsModule", back_populates="catalog_measures")
    imr_items = relationship("ImrItem", back_populates="measure")
    risk_measure_links = relationship("RiskMeasureLink", back_populates="measure")