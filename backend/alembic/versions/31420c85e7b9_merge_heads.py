"""merge_heads

Revision ID: 31420c85e7b9
Revises: 59ba4f69c258, add_organization_people
Create Date: 2026-05-10 21:56:46.333476

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '31420c85e7b9'
down_revision: Union[str, None] = 'add_organization_people'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass