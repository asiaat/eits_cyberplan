"""add requirement_profile todo_description cost_eur to imr_items

Revision ID: add_imr_requirement_profile_fields
Revises: 10c105bdb0dc
Create Date: 2026-05-21 20:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_imr_requirement_profile_fields'
down_revision: Union[str, Sequence[str], None] = '10c105bdb0dc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('imr_items', sa.Column('requirement_profile', sa.String(20), nullable=True))
    op.add_column('imr_items', sa.Column('todo_description', sa.Text(), nullable=True))
    op.add_column('imr_items', sa.Column('cost_eur', sa.Numeric(12, 2), nullable=True))


def downgrade() -> None:
    op.drop_column('imr_items', 'cost_eur')
    op.drop_column('imr_items', 'todo_description')
    op.drop_column('imr_items', 'requirement_profile')