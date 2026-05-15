"""Add division_id to business_processes.

Revision ID: add_bp_division_id
Revises: 31420c85e7b9
Create Date: 2025-05-15
"""
from alembic import op
import sqlalchemy as sa

revision = 'add_bp_division_id'
down_revision = '31420c85e7b9'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        'business_processes',
        sa.Column('division_id', sa.String(255), nullable=True)
    )


def downgrade():
    op.drop_column('business_processes', 'division_id')