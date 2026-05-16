"""Fix audit_logs FK to app_tenants."""
from alembic import op
import sqlalchemy as sa

revision = 'fix_audit_logs_fk_v2'
down_revision = '985a4a218e24'
branch_labels = None
depends_on = None


def upgrade():
    # Create FK constraints pointing to app_tenants and global_users
    op.create_foreign_key(
        'audit_logs_tenant_id_fkey',
        'audit_logs', 'app_tenants',
        ['tenant_id'], ['id'],
        ondelete='CASCADE'
    )
    op.create_foreign_key(
        'audit_logs_actor_user_id_fkey',
        'audit_logs', 'global_users',
        ['actor_user_id'], ['id']
    )


def downgrade():
    op.drop_constraint('audit_logs_actor_user_id_fkey', 'audit_logs', type_='foreignkey')
    op.drop_constraint('audit_logs_tenant_id_fkey', 'audit_logs', type_='foreignkey')