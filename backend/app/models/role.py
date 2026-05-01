"""Role model."""
from sqlalchemy import Column, String, Text
from sqlalchemy.orm import relationship

from app.db.base import Base


class Role(Base):
    __tablename__ = "roles"

    id = Column(Text, primary_key=True)
    code = Column(String(50), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text)

    memberships = relationship("Membership", back_populates="role")