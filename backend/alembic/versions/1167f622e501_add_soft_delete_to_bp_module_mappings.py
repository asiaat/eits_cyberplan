"""add soft delete to bp_module_mappings

Revision ID: 1167f622e501
Revises: f6e9ca149879
Create Date: 2026-05-29 16:18:22.089987

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '1167f622e501'
down_revision: Union[str, None] = 'f6e9ca149879'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'bp_module_mappings',
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        'bp_module_mappings',
        sa.Column('deleted_by', postgresql.UUID(), nullable=True),
    )
    op.create_index(
        'ix_bp_module_mappings_deleted_at',
        'bp_module_mappings',
        ['deleted_at'],
        postgresql_where=sa.text('deleted_at IS NULL'),
    )


def downgrade() -> None:
    op.drop_index('ix_bp_module_mappings_deleted_at', table_name='bp_module_mappings')
    op.drop_column('bp_module_mappings', 'deleted_by')
    op.drop_column('bp_module_mappings', 'deleted_at')