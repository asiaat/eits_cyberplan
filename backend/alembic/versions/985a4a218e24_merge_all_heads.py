"""merge all heads

Revision ID: 985a4a218e24
Revises: eabb7a7a082f, fix_business_process_tenant_fk
Create Date: 2026-05-16 07:27:47.980150

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '985a4a218e24'
down_revision: Union[str, None] = ('eabb7a7a082f', 'fix_business_process_tenant_fk')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass