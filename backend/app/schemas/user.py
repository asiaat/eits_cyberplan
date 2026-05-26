"""User schemas."""
from uuid import UUID

from pydantic import BaseModel


class TenantUser(BaseModel):
    """User with resolved tenant information."""

    id: UUID
    email: str
    name: str
    tenant_id: UUID
    role_code: str

    class Config:
        from_attributes = True
