"""Add remarks column to assets table.

Revision ID: add_asset_remarks
Revises: 
Create Date: 2026-05-17

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_asset_remarks'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('assets', sa.Column('remarks', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('assets', 'remarks')