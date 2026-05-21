"""add audit fields to imr_items

Revision ID: 120e01d715df
Revises: 10c105bdb0dc
Create Date: 2026-05-21 19:54:49.160487

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '120e01d715df'
down_revision: Union[str, Sequence[str], None] = '10c105bdb0dc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add audit fields to imr_items table
    op.add_column('imr_items', sa.Column('created_by', sa.UUID(), nullable=True))
    op.add_column('imr_items', sa.Column('updated_by', sa.UUID(), nullable=True))
    op.add_column('imr_items', sa.Column('status_changed_at', sa.DateTime(timezone=True), nullable=True))
    
    # Add foreign key constraints for created_by and updated_by
    op.create_foreign_key(
        'fk_imr_items_created_by',
        'imr_items', 'local_users',
        ['created_by'], ['id'],
        ondelete='SET NULL'
    )
    
    op.create_foreign_key(
        'fk_imr_items_updated_by',
        'imr_items', 'local_users',
        ['updated_by'], ['id'],
        ondelete='SET NULL'
    )
    
    # Add index for created_by for faster lookups
    op.create_index('ix_imr_items_created_by', 'imr_items', ['created_by'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_imr_items_created_by', table_name='imr_items')
    
    # Drop foreign key constraints
    op.drop_constraint('fk_imr_items_created_by', 'imr_items', type_='foreignkey')
    op.drop_constraint('fk_imr_items_updated_by', 'imr_items', type_='foreignkey')
    
    # Drop columns
    op.drop_column('imr_items', 'status_changed_at')
    op.drop_column('imr_items', 'updated_by')
    op.drop_column('imr_items', 'created_by')


def downgrade() -> None:
    pass