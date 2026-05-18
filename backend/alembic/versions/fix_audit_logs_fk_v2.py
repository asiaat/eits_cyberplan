"""Fix audit_logs FK to app_tenants."""
from alembic import op
import sqlalchemy as sa

revision = 'fix_audit_logs_fk_v2'
down_revision = '985a4a218e24'
branch_labels = None
depends_on = None


def upgrade():
    # Create FK constraints pointing to app_tenants and global_users (idempotent)
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_constraint WHERE conname = 'audit_logs_tenant_id_fkey'
            ) THEN
                ALTER TABLE audit_logs ADD CONSTRAINT audit_logs_tenant_id_fkey
                    FOREIGN KEY (tenant_id) REFERENCES app_tenants (id) ON DELETE CASCADE;
            END IF;
        END $$;
    """)
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_constraint WHERE conname = 'audit_logs_actor_user_id_fkey'
            ) THEN
                ALTER TABLE audit_logs ADD CONSTRAINT audit_logs_actor_user_id_fkey
                    FOREIGN KEY (actor_user_id) REFERENCES global_users (id);
            END IF;
        END $$;
    """)


def downgrade():
    op.drop_constraint('audit_logs_actor_user_id_fkey', 'audit_logs', type_='foreignkey')
    op.drop_constraint('audit_logs_tenant_id_fkey', 'audit_logs', type_='foreignkey')