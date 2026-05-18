"""mark fix_audit_logs_fk_v2 as applied (FKs created by earlier migration).

Revision ID: mark_fix_audit_logs_applied
Revises: 985a4a218e24
Create Date: 2026-05-18

The FK constraints audit_logs_tenant_id_fkey and audit_logs_actor_user_id_fkey
were already created by an earlier migration. This stub marks the FK fix as
applied so it doesn't fail on upgrade.
"""
from typing import Sequence, Union
from alembic import op

revision: str = 'mark_fix_audit_logs_applied'
down_revision: Union[str, None] = '985a4a218e24'
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass