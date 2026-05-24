"""Core utilities."""
from typing import TypeVar, Any

from sqlalchemy.orm import Query

from app.db.base import SoftDeleteMixin


M = TypeVar("M", bound=SoftDeleteMixin)


def active_query(query: Query, model: type[M]) -> Query:
    """Filter query to exclude soft-deleted records."""
    return query.filter(model.deleted_at.is_(None))
