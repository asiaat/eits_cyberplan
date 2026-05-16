"""Add divisions column to app_tenants table."""
from alembic import op
import sqlalchemy as sa

revision = 'add_app_tenant_divisions'
down_revision = 'add_app_tenant_org_fields'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('app_tenants', sa.Column('divisions', sa.String(5000), nullable=True))


def downgrade():
    op.drop_column('app_tenants', 'divisions')