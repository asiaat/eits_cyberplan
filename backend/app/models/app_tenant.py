"""AppTenant models - Tier A subscription layer."""
import uuid

from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class AppTenant(Base):
    """Subscription registry - Tier A."""
    __tablename__ = "app_tenants"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    status = Column(String(50), default="active")
    plan = Column(String(50))  # free, standard, enterprise
    created_at = Column(DateTime, server_default="now()")

    tenant_users = relationship("TenantUser", back_populates="tenant", foreign_keys="TenantUser.tenant_id")
    local_users = relationship("LocalUser", back_populates="tenant")
    e_its_roles = relationship("EITSRole", back_populates="tenant")


class GlobalUser(Base):
    """Central identity - Tier A. Shared across all tenants."""
    __tablename__ = "global_users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    mfa_enabled = Column(Boolean, default=False)
    mfa_secret = Column(String(255), nullable=True)  # encrypted TOTP secret
    created_at = Column(DateTime, server_default="now()")

    tenant_users = relationship("TenantUser", back_populates="user", foreign_keys="TenantUser.user_id")
    local_users = relationship("LocalUser", back_populates="global_user")


class TenantUser(Base):
    """Maps user to tenant subscription - Tier A."""
    __tablename__ = "tenant_users"

    tenant_id = Column(UUID(as_uuid=True), ForeignKey("app_tenants.id", ondelete="CASCADE"), primary_key=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("global_users.id", ondelete="CASCADE"), primary_key=True)
    assigned_at = Column(DateTime, server_default="now()")

    tenant = relationship("AppTenant", back_populates="tenant_users")
    user = relationship("GlobalUser", back_populates="tenant_users")