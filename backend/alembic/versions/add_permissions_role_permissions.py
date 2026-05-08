"""Add permissions and role_permissions tables

Revision ID: add_permissions_role_permissions
Revises: d5f98c5b3584
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_permissions_role_permissions'
down_revision: Union[str, None] = 'd5f98c5b3584'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create permissions table
    op.create_table(
        'permissions',
        sa.Column('id', sa.Text(), primary_key=True),
        sa.Column('code', sa.String(100), unique=True, nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('category', sa.String(50), nullable=True),
    )
    
    # Create role_permissions junction table
    op.create_table(
        'role_permissions',
        sa.Column('role_id', sa.Text(), sa.ForeignKey('roles.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('permission_id', sa.Text(), sa.ForeignKey('permissions.id', ondelete='CASCADE'), primary_key=True),
    )
    
    # Add is_default column to roles (if not exists)
    op.execute("ALTER TABLE roles ADD COLUMN IF NOT EXISTS is_default VARCHAR(10) DEFAULT 'false'")


def downgrade() -> None:
    op.drop_table('role_permissions')
    op.drop_table('permissions')
    op.execute("ALTER TABLE roles DROP COLUMN IF EXISTS is_default")