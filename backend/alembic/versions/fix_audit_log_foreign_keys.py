"""Fix audit_log foreign keys to app_tenants and global_users."""
from alembic import op
import sqlalchemy as sa

revision = 'fix_audit_log_foreign_keys'
down_revision = 'add_app_tenant_divisions'
branch_labels = None
depends_on = None


def upgrade():
    op.create_foreign_key(
        'audit_logs_tenant_id_fkey_new',
        'audit_logs', 'app_tenants',
        ['tenant_id'], ['id'],
        ondelete='CASCADE'
    )
    op.create_foreign_key(
        'audit_logs_actor_user_id_fkey_new',
        'audit_logs', 'global_users',
        ['actor_user_id'], ['id']
    )


def downgrade():
    op.drop_constraint('audit_logs_actor_user_id_fkey_new', 'audit_logs', type_='foreignkey')
    op.drop_constraint('audit_logs_tenant_id_fkey_new', 'audit_logs', type_='foreignkey')