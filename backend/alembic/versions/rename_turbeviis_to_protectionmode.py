"""Rename turbeviis_selections table and indexes to protectionmode_selections.

Revision ID: rename_to_protectionmode
Revises: fix_turbeviis_constraint
Create Date: 2026-05-21
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = 'rename_to_protectionmode'
down_revision: Union[str, None] = 'fix_turbeviis_constraint'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Rename table
    op.rename_table('turbeviis_selections', 'protectionmode_selections')

    # Rename indexes
    op.execute("ALTER INDEX ix_turbeviis_tenant_id RENAME TO ix_protectionmode_tenant_id")
    op.execute("ALTER INDEX ix_turbeviis_catalog_version RENAME TO ix_protectionmode_catalog_version")
    op.execute("ALTER INDEX ix_turbeviis_security_approach RENAME TO ix_protectionmode_security_approach")
    op.execute("ALTER INDEX ix_turbeviis_is_active RENAME TO ix_protectionmode_is_active")

    # Rename remaining unique constraint (uq_turbeviis_tenant_active was already dropped in fix_turbeviis_constraint)
    op.execute(
        "ALTER TABLE protectionmode_selections "
        "RENAME CONSTRAINT uq_turbeviis_tenant_catalog TO uq_protectionmode_tenant_catalog"
    )


def downgrade() -> None:
    # Reverse constraint rename
    op.execute(
        "ALTER TABLE protectionmode_selections "
        "RENAME CONSTRAINT uq_protectionmode_tenant_catalog TO uq_turbeviis_tenant_catalog"
    )

    # Reverse index renames
    op.execute("ALTER INDEX ix_protectionmode_is_active RENAME TO ix_turbeviis_is_active")
    op.execute("ALTER INDEX ix_protectionmode_security_approach RENAME TO ix_turbeviis_security_approach")
    op.execute("ALTER INDEX ix_protectionmode_catalog_version RENAME TO ix_turbeviis_catalog_version")
    op.execute("ALTER INDEX ix_protectionmode_tenant_id RENAME TO ix_turbeviis_tenant_id")

    # Rename table back
    op.rename_table('protectionmode_selections', 'turbeviis_selections')
