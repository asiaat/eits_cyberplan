"""merge all heads

Revision ID: 15dd342acd17
Revises: 170d56dff76b, remove_mapped_module_id_dual_fk
Create Date: 2026-06-06 13:49:37.518103

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '15dd342acd17'
down_revision: Union[str, None] = ('170d56dff76b', 'remove_mapped_module_id_dual_fk')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass