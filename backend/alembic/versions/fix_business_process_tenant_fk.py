"""Fix business_processes tenant_id to use app_tenants."""
from alembic import op
import sqlalchemy as sa

revision = 'fix_business_process_tenant_fk'
down_revision = 'fe97372b7f1a'
branch_labels = None
depends_on = None


def upgrade():
    # Drop old FK and create new one pointing to app_tenants
    op.drop_constraint('business_processes_tenant_id_fkey', 'business_processes', type_='foreignkey')
    op.create_foreign_key(
        'business_processes_tenant_id_fkey_new',
        'business_processes', 'app_tenants',
        ['tenant_id'], ['id'],
        ondelete='CASCADE'
    )


def downgrade():
    op.drop_constraint('business_processes_tenant_id_fkey_new', 'business_processes', type_='foreignkey')
    op.create_foreign_key(
        'business_processes_tenant_id_fkey',
        'business_processes', 'tenants',
        ['tenant_id'], ['id'],
        ondelete='CASCADE'
    )