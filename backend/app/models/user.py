"""User model."""
import uuid

from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    auth_provider = Column(String(50), default="local")
    hashed_password = Column(String(255))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default="now()")

    memberships = relationship("Membership", back_populates="user")
    owned_business_processes = relationship(
        "BusinessProcess", back_populates="owner_user", foreign_keys="BusinessProcess.owner_user_id"
    )
    owned_assets = relationship("Asset", back_populates="owner_user", foreign_keys="Asset.owner_user_id")
    owned_implementation_items = relationship(
        "ImplementationPlanItem", back_populates="owner_user"
    )
    owned_risks = relationship("Risk", back_populates="owner_user")
    owned_evidences = relationship("Evidence", back_populates="owner_user")
    mappings = relationship("ObjectModuleMapping", back_populates="selected_by_user")
    comments = relationship("Comment", back_populates="author_user")