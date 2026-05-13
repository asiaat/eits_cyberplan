"""merge 31420c85e7b9 and create_persons_tables

Revision ID: merge_persons_head
Revises: 31420c85e7b9, create_persons_tables
Create Date: 2026-05-10 22:30:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = 'merge_persons_head'
down_revision: Union[str, None] = ('31420c85e7b9', 'create_persons_tables')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass