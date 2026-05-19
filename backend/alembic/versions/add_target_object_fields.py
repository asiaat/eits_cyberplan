"""Add target object fields to assets table.

Revision ID: add_target_object_fields
Revises:
Create Date: 2026-05-19

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_target_object_fields'
down_revision = 'v4_etl_compatibility'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('assets', sa.Column('is_grouped', sa.Boolean(), server_default='false', nullable=False))
    op.add_column('assets', sa.Column('quantity', sa.Integer(), server_default='1', nullable=False))
    op.add_column('assets', sa.Column('group_name', sa.String(255), nullable=True))


def downgrade() -> None:
    op.drop_column('assets', 'group_name')
    op.drop_column('assets', 'quantity')
    op.drop_column('assets', 'is_grouped')
