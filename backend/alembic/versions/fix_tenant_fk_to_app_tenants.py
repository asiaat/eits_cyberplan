"""Fix tenant_id foreign keys to reference app_tenants.

Revision ID: fix_tenant_fk_to_app_tenants
Revises:
Create Date: 2026-06-06
"""
from alembic import op
import sqlalchemy as sa


# Tables that have tenant_id FK pointing to wrong tenants table
TABLES_WITH_TENANT_FK = [
    "assets",
    "asset_relations",
    "comments",
    "evidences",
    "evidence_links",
    "implementation_plan_items",
    "memberships",
    "object_module_mappings",
    "organization_people",
    "person_organizations",
    "process_assets",
    "risks",
]


def upgrade() -> None:
    for table in TABLES_WITH_TENANT_FK:
        constraint_name = f"{table}_tenant_id_fkey"
        # Drop old FK pointing to tenants table
        op.execute(f'ALTER TABLE {table} DROP CONSTRAINT IF EXISTS {constraint_name}')
        # Add new FK pointing to app_tenants
        op.execute(f'''
            ALTER TABLE {table}
            ADD CONSTRAINT {constraint_name}
            FOREIGN KEY (tenant_id) REFERENCES app_tenants(id)
        ''')
        print(f"Fixed {table}.tenant_id FK → app_tenants")


def downgrade() -> None:
    for table in TABLES_WITH_TENANT_FK:
        constraint_name = f"{table}_tenant_id_fkey"
        op.execute(f'ALTER TABLE {table} DROP CONSTRAINT IF EXISTS {constraint_name}')
        op.execute(f'''
            ALTER TABLE {table}
            ADD CONSTRAINT {constraint_name}
            FOREIGN KEY (tenant_id) REFERENCES tenants(id)
        ''')
        print(f"Reverted {table}.tenant_id FK → tenants")