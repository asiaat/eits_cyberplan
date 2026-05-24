"""remove mapped_module_id and dual fk constraints from imr_items

Revision ID: remove_mapped_module_id_dual_fk
Revises: 10c105bdb0dc
Create Date: 2026-05-24 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'remove_mapped_module_id_dual_fk'
down_revision: Union[str, Sequence[str], None] = '10c105bdb0dc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_index('ix_imr_items_mapped_module_id', table_name='imr_items')
    op.drop_constraint('fk_imr_items_mapped_module_asset', 'imr_items', type_='foreignkey')
    op.drop_constraint('fk_imr_items_mapped_module_bp', 'imr_items', type_='foreignkey')
    op.drop_column('imr_items', 'mapped_module_id')


def downgrade() -> None:
    op.add_column('imr_items', sa.Column('mapped_module_id', sa.UUID(), nullable=True))
    op.create_index('ix_imr_items_mapped_module_id', 'imr_items', ['mapped_module_id'])
    op.create_foreign_key(
        'fk_imr_items_mapped_module_asset',
        'imr_items', 'asset_module_mappings',
        ['mapped_module_id'], ['id'],
        ondelete='CASCADE'
    )
    op.create_foreign_key(
        'fk_imr_items_mapped_module_bp',
        'imr_items', 'bp_module_mappings',
        ['mapped_module_id'], ['id'],
        ondelete='CASCADE'
    )