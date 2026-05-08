"""Role-Permission junction model."""
from sqlalchemy import Column, String, ForeignKey, Text
from sqlalchemy.orm import relationship

from app.db.base import Base


class RolePermission(Base):
    __tablename__ = "role_permissions"

    role_id = Column(Text, ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True)
    permission_id = Column(Text, ForeignKey("permissions.id", ondelete="CASCADE"), primary_key=True)

    role = relationship("Role", back_populates="role_permissions")
    permission = relationship("Permission", back_populates="role_permissions")