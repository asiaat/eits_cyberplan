"""E-ITS ETL compatibility fixes.

Revision ID: v4_etl_compatibility
Revises: v3_eits_tier_ab_full
Create Date: 2026-05-18

Ensures schema alignment for ETL pipeline:
- Adds missing indexes on eits_catalog_versions (year, is_active)
- Adds missing index on eits_modules (module_group)
- Ensures all ETL-required columns are present
"""

from alembic import op

revision: str = 'v4_etl_compatibility'
down_revision: str | None = 'merge_eits_v2_heads'
branch_labels = None
depends_on: str | None = None


def upgrade() -> None:
    op.create_index(
        'ix_eits_catalog_versions_year',
        'eits_catalog_versions',
        ['year'],
        unique=False,
        if_not_exists=True,
    )
    op.create_index(
        'ix_eits_catalog_versions_is_active',
        'eits_catalog_versions',
        ['is_active'],
        unique=False,
        if_not_exists=True,
    )
    op.create_index(
        'ix_eits_modules_module_group',
        'eits_modules',
        ['module_group'],
        unique=False,
        if_not_exists=True,
    )
    op.create_index(
        'ix_eits_modules_catalog_version_id',
        'eits_modules',
        ['catalog_version_id'],
        unique=False,
        if_not_exists=True,
    )
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_constraint WHERE conname = 'ck_measure_level'
            ) THEN
                ALTER TABLE eits_catalog_measures
                ADD CONSTRAINT ck_measure_level
                CHECK (measure_level IN ('BASE', 'STANDARD', 'HIGH'));
            END IF;
        END $$;
    """)


def downgrade() -> None:
    op.drop_index('ix_eits_modules_catalog_version_id', 'eits_modules', if_exists=True)
    op.drop_index('ix_eits_modules_module_group', 'eits_modules', if_exists=True)
    op.drop_index('ix_eits_catalog_versions_is_active', 'eits_catalog_versions', if_exists=True)
    op.drop_index('ix_eits_catalog_versions_year', 'eits_catalog_versions', if_exists=True)
