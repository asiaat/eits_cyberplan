"""Add referential integrity constraints for persons FK.

Revision ID: add_person_fk_restrict
Revises: merge_persons_head
Create Date: 2026-05-11 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = 'add_person_fk_restrict'
down_revision: Union[str, None] = 'merge_persons_head'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_constraint('assets_person_id_fkey', 'assets', type_='foreignkey')
    op.create_foreign_key(
        'assets_person_id_fkey', 'assets', 'persons',
        ['person_id'], ['id'],
        ondelete='RESTRICT'
    )

    op.drop_constraint('person_organizations_person_id_fkey', 'person_organizations', type_='foreignkey')
    op.create_foreign_key(
        'person_organizations_person_id_fkey', 'person_organizations', 'persons',
        ['person_id'], ['id'],
        ondelete='RESTRICT'
    )


def downgrade() -> None:
    op.drop_constraint('person_organizations_person_id_fkey', 'person_organizations', type_='foreignkey')
    op.create_foreign_key(
        'person_organizations_person_id_fkey', 'person_organizations', 'persons',
        ['person_id'], ['id'],
        ondelete='CASCADE'
    )

    op.drop_constraint('assets_person_id_fkey', 'assets', type_='foreignkey')
    op.create_foreign_key(
        'assets_person_id_fkey', 'assets', 'persons',
        ['person_id'], ['id'],
        ondelete='CASCADE'
    )