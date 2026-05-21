"""add mapped_module_id to imr_items

Revision ID: 10c105bdb0dc
Revises: add_scope_modeling
Create Date: 2026-05-21 19:11:48.339699

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '10c105bdb0dc'
down_revision: Union[str, Sequence[str], None] = 'add_scope_modeling'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add mapped_module_id column to imr_items table
    op.add_column('imr_items', sa.Column('mapped_module_id', sa.UUID(), nullable=True))
    
    # Add foreign key constraints to both asset_module_mappings and bp_module_mappings
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
    
    # Add indexes for performance
    op.create_index('ix_imr_items_mapped_module_id', 'imr_items', ['mapped_module_id'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_imr_items_mapped_module_id', table_name='imr_items')
    
    # Drop foreign key constraints
    op.drop_constraint('fk_imr_items_mapped_module_asset', 'imr_items', type_='foreignkey')
    op.drop_constraint('fk_imr_items_mapped_module_bp', 'imr_items', type_='foreignkey')
    
    # Drop column
    op.drop_column('imr_items', 'mapped_module_id')


def downgrade() -> None:
    pass