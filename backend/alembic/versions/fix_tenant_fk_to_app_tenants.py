"""Fix tenant_id foreign keys to reference app_tenants.

Revision ID: fix_tenant_fk_to_app_tenants
Revises:
Create Date: 2026-06-06
"""
from alembic import op
import sqlalchemy as sa


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
        result = op.execute(f'''
            SELECT ccu.table_name
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu
              ON tc.constraint_name = kcu.constraint_name
            JOIN information_schema.constraint_column_usage ccu
              ON ccu.constraint_name = tc.constraint_name
            WHERE tc.constraint_type = 'FOREIGN KEY'
              AND kcu.table_name = '{table}'
              AND kcu.column_name = 'tenant_id'
        ''').fetchone()

        if result is None:
            print(f"{table}.tenant_id: no FK constraint found, skipping")
            continue

        current_target = result[0]
        if current_target == "app_tenants":
            print(f"{table}.tenant_id: already points to app_tenants, skipping")
            continue
        elif current_target == "tenants":
            op.execute(f'ALTER TABLE {table} DROP CONSTRAINT {constraint_name}')
            op.execute(f'''
                ALTER TABLE {table}
                ADD CONSTRAINT {constraint_name}
                FOREIGN KEY (tenant_id) REFERENCES app_tenants(id)
            ''')
            print(f"{table}.tenant_id: migrated tenants -> app_tenants")
        else:
            print(f"{table}.tenant_id: points to {current_target}, not touching")


def downgrade() -> None:
    for table in TABLES_WITH_TENANT_FK:
        constraint_name = f"{table}_tenant_id_fkey"
        result = op.execute(f'''
            SELECT ccu.table_name
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu
              ON tc.constraint_name = kcu.constraint_name
            JOIN information_schema.constraint_column_usage ccu
              ON ccu.constraint_name = tc.constraint_name
            WHERE tc.constraint_type = 'FOREIGN KEY'
              AND kcu.table_name = '{table}'
              AND kcu.column_name = 'tenant_id'
        ''').fetchone()

        if result is None:
            print(f"{table}.tenant_id: no FK constraint found, skipping")
            continue

        current_target = result[0]
        if current_target == "tenants":
            print(f"{table}.tenant_id: already points to tenants, skipping")
            continue
        elif current_target == "app_tenants":
            op.execute(f'ALTER TABLE {table} DROP CONSTRAINT {constraint_name}')
            op.execute(f'''
                ALTER TABLE {table}
                ADD CONSTRAINT {constraint_name}
                FOREIGN KEY (tenant_id) REFERENCES tenants(id)
            ''')
            print(f"{table}.tenant_id: reverted app_tenants -> tenants")