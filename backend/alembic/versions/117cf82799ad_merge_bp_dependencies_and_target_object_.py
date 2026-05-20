"""merge_bp_dependencies_and_target_object_fields

Revision ID: 117cf82799ad
Revises: add_bp_dependencies, add_target_object_fields
Create Date: 2026-05-20 14:51:53.456968

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '117cf82799ad'
down_revision: Union[str, None] = ('add_bp_dependencies', 'add_target_object_fields')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass