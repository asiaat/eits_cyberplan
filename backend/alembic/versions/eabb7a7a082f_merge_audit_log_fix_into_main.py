"""merge audit_log fix into main

Revision ID: eabb7a7a082f
Revises: fe97372b7f1a, fix_audit_log_foreign_keys
Create Date: 2026-05-16 07:22:33.323550

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'eabb7a7a082f'
down_revision: Union[str, None] = ('fe97372b7f1a', 'fix_audit_log_foreign_keys')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass