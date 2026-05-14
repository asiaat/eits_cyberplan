"""E-ITS Role Permission junction model."""
import uuid

from sqlalchemy import Column, String, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class EITSRolePermission(Base):
    __tablename__ = "e_its_role_permissions"

    role_id = Column(UUID(as_uuid=True), ForeignKey("e_its_roles.id", ondelete="CASCADE"), primary_key=True)
    permission_id = Column(Text, ForeignKey("permissions.id", ondelete="CASCADE"), primary_key=True)

    role = relationship("EITSRole", back_populates="role_permissions")
    permission = relationship("Permission", back_populates="e_its_role_permissions")