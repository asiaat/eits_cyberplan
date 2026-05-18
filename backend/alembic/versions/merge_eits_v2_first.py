"""merge eits v2 first head

Revision ID: merge_eits_v2_first
Revises: add_asset_remarks, fix_audit_logs_fk_v2
Create Date: 2026-05-18

Merges the two parallel branches that originated from the base.
"""
from typing import Sequence, Union
from alembic import op

revision: str = 'merge_eits_v2_first'
down_revision: Union[str, Sequence[str], None] = ('add_asset_remarks', 'fix_audit_logs_fk_v2')
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass