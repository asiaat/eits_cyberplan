"""merge eits v2 second head

Revision ID: merge_eits_v2_base
Revises: merge_eits_v2_first, v3_eits_tier_ab_full
Create Date: 2026-05-18
"""
from typing import Sequence, Union
from alembic import op

revision: str = 'merge_eits_v2_base'
down_revision: Union[str, Sequence[str], None] = ('merge_eits_v2_first', 'v3_eits_tier_ab_full')
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass