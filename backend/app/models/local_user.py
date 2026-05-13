"""LocalUser and EITSRole models - Tier B per-tenant."""
import uuid

from sqlalchemy import Column, String, Boolean, DateTime, Text, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class LocalUser(Base):
    """Per-tenant user profile - Tier B."""
    __tablename__ = "local_users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    global_user_id = Column(UUID(as_uuid=True), ForeignKey("global_users.id", ondelete="CASCADE"), nullable=False)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("app_tenants.id", ondelete="CASCADE"), nullable=False)
    full_name = Column(String(255), nullable=False)
    department = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default="now()")

    __table_args__ = (UniqueConstraint("global_user_id", "tenant_id", name="uq_local_user_global_tenant"),)

    global_user = relationship("GlobalUser", back_populates="local_users")
    tenant = relationship("AppTenant", back_populates="local_users")
    memberships = relationship("Membership", back_populates="local_user")


class EITSRole(Base):
    """E-ITS standard roles - Tier B. Per-tenant."""
    __tablename__ = "e_its_roles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("app_tenants.id", ondelete="CASCADE"), nullable=False)
    role_name = Column(String(100), nullable=False)
    description = Column(Text)

    __table_args__ = (UniqueConstraint("tenant_id", "role_name", name="uq_e_its_role_tenant"),)

    tenant = relationship("AppTenant", back_populates="e_its_roles")
    user_roles = relationship("UserRole", back_populates="e_its_role")
    role_permissions = relationship("EITSRolePermission", back_populates="role")


class UserRole(Base):
    """User role assignments - Tier B. Links LocalUser to EITSRole."""
    __tablename__ = "user_roles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("local_users.id", ondelete="CASCADE"), nullable=False)
    role_id = Column(UUID(as_uuid=True), ForeignKey("e_its_roles.id", ondelete="CASCADE"), nullable=False)
    granted_by = Column(UUID(as_uuid=True), ForeignKey("local_users.id"), nullable=True)
    granted_at = Column(DateTime, server_default="now()")

    local_user = relationship("LocalUser", foreign_keys=[user_id])
    granted_by_user = relationship("LocalUser", foreign_keys=[granted_by])
    e_its_role = relationship("EITSRole", back_populates="user_roles")