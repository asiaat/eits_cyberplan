"""Migrate asset_type 'person' to 'competence'.

Revision ID: v5_migrate_asset_type_person_to_competence
Revises: v4_etl_compatibility
Create Date: 2026-06-07

Updates existing assets where asset_type = 'person' to asset_type = 'competence'.
"""

from alembic import op

revision: str = 'v5_migrate_asset_type_person_to_competence'
down_revision: str | None = 'v4_etl_compatibility'
branch_labels = None
depends_on: str | None = None


def upgrade() -> None:
    op.execute("UPDATE assets SET asset_type = 'competence' WHERE asset_type = 'person'")


def downgrade() -> None:
    op.execute("UPDATE assets SET asset_type = 'person' WHERE asset_type = 'competence'")
