"""Fix turbeviis_selections constraint for is_active.

Revision ID: fix_turbeviis_constraint
Revises: add_turbeviis_selections
Create Date: 2026-05-21

The unique constraint on (tenant_id, is_active) was preventing
deactivation since multiple rows with is_active=false would violate it.
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'fix_turbeviis_constraint'
down_revision: Union[str, None] = 'add_turbeviis_selections'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_constraint('uq_turbeviis_tenant_active', 'turbeviis_selections', type_='unique')


def downgrade() -> None:
    op.create_unique_constraint('uq_turbeviis_tenant_active', 'turbeviis_selections', ['tenant_id', 'is_active'])