"""add_imr_snapshots

Revision ID: 170d56dff76b
Revises: add_soft_delete_columns
Create Date: 2026-05-24 05:54:42.732788

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '170d56dff76b'
down_revision: Union[str, None] = 'add_soft_delete_columns'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('imr_snapshots',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('protection_mode_selection_id', sa.UUID(), nullable=True),
        sa.Column('label', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_current', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('item_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_by', sa.UUID(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('restored_from', sa.UUID(), nullable=True),
        sa.ForeignKeyConstraint(['created_by'], ['local_users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['protection_mode_selection_id'], ['protectionmode_selections.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['tenant_id'], ['app_tenants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_imr_snapshots_tenant_id'), 'imr_snapshots', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_imr_snapshots_pm_selection_id'), 'imr_snapshots', ['protection_mode_selection_id'], unique=False)

    op.add_column('imr_items', sa.Column('imr_snapshot_id', sa.UUID(), nullable=True))
    op.create_index(op.f('ix_imr_items_imr_snapshot_id'), 'imr_items', ['imr_snapshot_id'], unique=False)
    op.create_foreign_key('fk_imr_items_imr_snapshot_id', 'imr_items', 'imr_snapshots', ['imr_snapshot_id'], ['id'], ondelete='SET NULL')


def downgrade() -> None:
    op.drop_constraint('fk_imr_items_imr_snapshot_id', 'imr_items', type_='foreignkey')
    op.drop_index(op.f('ix_imr_items_imr_snapshot_id'), table_name='imr_items')
    op.drop_column('imr_items', 'imr_snapshot_id')

    op.drop_index(op.f('ix_imr_snapshots_pm_selection_id'), table_name='imr_snapshots')
    op.drop_index(op.f('ix_imr_snapshots_tenant_id'), table_name='imr_snapshots')
    op.drop_table('imr_snapshots')
