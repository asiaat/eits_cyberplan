"""add soft delete columns to domain models

Revision ID: add_soft_delete_columns
Revises: 47a801ddd3a5
Create Date: 2026-05-24 08:15:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = 'add_soft_delete_columns'
down_revision: Union[str, None] = '47a801ddd3a5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


TABLES = [
    'assets',
    'business_processes',
    'risks',
    'evidences',
    'imr_items',
    'damage_assessments',
    'protectionmode_selections',
    'security_profiles',
    'persons',
]


def upgrade() -> None:
    for table in TABLES:
        op.add_column(
            table,
            sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        )
        op.add_column(
            table,
            sa.Column('deleted_by', postgresql.UUID(), nullable=True),
        )
        op.create_index(
            f'ix_{table}_deleted_at',
            table,
            ['deleted_at'],
            postgresql_where=sa.text('deleted_at IS NULL'),
        )


def downgrade() -> None:
    for table in TABLES:
        op.drop_index(f'ix_{table}_deleted_at', table_name=table)
        op.drop_column(table, 'deleted_by')
        op.drop_column(table, 'deleted_at')
