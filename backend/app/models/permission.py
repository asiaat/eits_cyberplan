"""Permission model."""
from sqlalchemy import Column, String, Text
from sqlalchemy.orm import relationship

from app.db.base import Base


class Permission(Base):
    __tablename__ = "permissions"

    id = Column(Text, primary_key=True)
    code = Column(String(100), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    category = Column(String(50))  # e.g., "users", "processes", "assets", "risks", "evidence", "dashboard", "audit"

    role_permissions = relationship("RolePermission", back_populates="permission")
    e_its_role_permissions = relationship("EITSRolePermission", back_populates="permission")