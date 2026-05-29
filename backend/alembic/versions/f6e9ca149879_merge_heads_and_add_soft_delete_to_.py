"""merge heads and add soft delete to asset_module_mappings

Revision ID: f6e9ca149879
Revises: 170d56dff76b, remove_mapped_module_id_dual_fk
Create Date: 2026-05-29 15:02:17.066903

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'f6e9ca149879'
down_revision: Union[str, None] = ('170d56dff76b', 'remove_mapped_module_id_dual_fk')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'asset_module_mappings',
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        'asset_module_mappings',
        sa.Column('deleted_by', postgresql.UUID(), nullable=True),
    )
    op.create_index(
        'ix_asset_module_mappings_deleted_at',
        'asset_module_mappings',
        ['deleted_at'],
        postgresql_where=sa.text('deleted_at IS NULL'),
    )


def downgrade() -> None:
    op.drop_index('ix_asset_module_mappings_deleted_at', table_name='asset_module_mappings')
    op.drop_column('asset_module_mappings', 'deleted_by')
    op.drop_column('asset_module_mappings', 'deleted_at')