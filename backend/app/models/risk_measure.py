"""Risk-Measure relation model."""
import uuid

from sqlalchemy import Column, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base

# Note: This is a placeholder for risk-measure relations via risk_measure table