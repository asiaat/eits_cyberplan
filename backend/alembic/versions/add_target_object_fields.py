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
    op.execute("ALTER TABLE assets ADD COLUMN IF NOT EXISTS is_grouped BOOLEAN DEFAULT 'false' NOT NULL")
    op.execute("ALTER TABLE assets ADD COLUMN IF NOT EXISTS quantity INTEGER DEFAULT 1 NOT NULL")
    op.execute("ALTER TABLE assets ADD COLUMN IF NOT EXISTS group_name VARCHAR(255)")


def downgrade() -> None:
    op.drop_column('assets', 'group_name')
    op.drop_column('assets', 'quantity')
    op.drop_column('assets', 'is_grouped')
