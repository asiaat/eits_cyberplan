"""Add is_core field to assets table for CORE mode filtering.

Revision ID: add_asset_is_core_field
Revises: 10c105bdb0dc
Create Date: 2026-05-21

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'add_asset_is_core_field'
down_revision: Union[str, Sequence[str], None] = '10c105bdb0dc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('assets', sa.Column('is_core', sa.Boolean(), server_default='false', nullable=False))


def downgrade() -> None:
    op.drop_column('assets', 'is_core')