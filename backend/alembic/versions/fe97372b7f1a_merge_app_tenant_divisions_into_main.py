"""merge app_tenant_divisions into main

Revision ID: fe97372b7f1a
Revises: 095e742d6556, add_app_tenant_divisions
Create Date: 2026-05-16 07:03:49.767070

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'fe97372b7f1a'
down_revision: Union[str, None] = ('095e742d6556', 'add_app_tenant_divisions')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass