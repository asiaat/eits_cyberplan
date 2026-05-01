"""E-ITS Module-Measure relation model."""
import uuid

from sqlalchemy import Column, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class EitsModuleMeasure(Base):
    __tablename__ = "eits_module_measures"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    module_id = Column(UUID(as_uuid=True), ForeignKey("eits_modules.id"), nullable=False)
    measure_id = Column(UUID(as_uuid=True), ForeignKey("eits_measures.id"), nullable=False)

    module = relationship("EitsModule", back_populates="measures")
    measure = relationship("EitsMeasure", back_populates="modules")