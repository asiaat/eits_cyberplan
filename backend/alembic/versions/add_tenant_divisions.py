"""Add divisions column to tenants table."""
from alembic import op
import sqlalchemy as sa

revision = 'add_tenant_divisions'
down_revision = 'add_permissions_role_permissions'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('tenants', sa.Column('divisions', sa.JSON(), nullable=True))


def downgrade():
    op.drop_column('tenants', 'divisions')