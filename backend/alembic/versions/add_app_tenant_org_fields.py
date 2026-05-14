"""Add organization fields to app_tenants table."""
from alembic import op
import sqlalchemy as sa

revision = 'add_app_tenant_org_fields'
down_revision = 'e_its_role_permissions_v1'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('app_tenants', sa.Column('registry_code', sa.String(50), nullable=True))
    op.add_column('app_tenants', sa.Column('legal_form', sa.String(255), nullable=True))
    op.add_column('app_tenants', sa.Column('registered_address', sa.String(500), nullable=True))
    op.add_column('app_tenants', sa.Column('phone', sa.String(50), nullable=True))
    op.add_column('app_tenants', sa.Column('email', sa.String(255), nullable=True))


def downgrade():
    op.drop_column('app_tenants', 'email')
    op.drop_column('app_tenants', 'phone')
    op.drop_column('app_tenants', 'registered_address')
    op.drop_column('app_tenants', 'legal_form')
    op.drop_column('app_tenants', 'registry_code')