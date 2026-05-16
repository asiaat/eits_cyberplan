"""merge_add_bp_division_id

Revision ID: 095e742d6556
Revises: add_app_tenant_org_fields, add_bp_division_id
Create Date: 2026-05-15 09:00:58.571706

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '095e742d6556'
down_revision: Union[str, None] = ('add_app_tenant_org_fields', 'add_bp_division_id')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass