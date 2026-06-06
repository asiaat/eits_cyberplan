"""Merge remaining heads

Revision ID: 75d23bd52ea3
Revises: 170d56dff76b, remove_mapped_module_id_dual_fk
Create Date: 2026-06-06 11:30:22.374657

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '75d23bd52ea3'
down_revision: Union[str, Sequence[str], None] = ('170d56dff76b', 'remove_mapped_module_id_dual_fk')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
