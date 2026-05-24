"""Database session and base."""
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime
from sqlalchemy.dialects.postgresql import UUID

from app.db.session import Base


class SoftDeleteMixin:
    """Mixin for soft-deletable models.

    Adds deleted_at and deleted_by columns.
    All list queries should filter with .filter(Model.deleted_at.is_(None)).
    """
    deleted_at = Column(DateTime(timezone=True), nullable=True, index=True)
    deleted_by = Column(UUID(as_uuid=True), nullable=True)

    def soft_delete(self, by_user_id=None):
        self.deleted_at = datetime.now(timezone.utc)
        if by_user_id:
            self.deleted_by = by_user_id

    @property
    def is_deleted(self):
        return self.deleted_at is not None