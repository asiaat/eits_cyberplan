"""Rename remaining turbeviis_* constraints on protectionmode_selections.

Revision ID: cleanup_pm_constraints
Revises: rename_to_protectionmode
Create Date: 2026-05-21
"""
from typing import Sequence, Union
from alembic import op


revision: str = 'cleanup_pm_constraints'
down_revision: Union[str, None] = 'rename_to_protectionmode'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


TABLE = "protectionmode_selections"
OLD = "turbeviis_selections"
NEW = "protectionmode_selections"

CONSTRAINTS = [
    ("pkey", "PRIMARY KEY"),
    ("tenant_id_fkey", "FOREIGN KEY"),
    ("catalog_version_id_fkey", "FOREIGN KEY"),
    ("evidence_id_fkey", "FOREIGN KEY"),
    ("approved_by_fkey", "FOREIGN KEY"),
]


def upgrade() -> None:
    for suffix, _ctype in CONSTRAINTS:
        op.execute(
            f"ALTER TABLE {TABLE} "
            f"RENAME CONSTRAINT {OLD}_{suffix} TO {NEW}_{suffix}"
        )


def downgrade() -> None:
    for suffix, _ctype in reversed(CONSTRAINTS):
        op.execute(
            f"ALTER TABLE {TABLE} "
            f"RENAME CONSTRAINT {NEW}_{suffix} TO {OLD}_{suffix}"
        )
