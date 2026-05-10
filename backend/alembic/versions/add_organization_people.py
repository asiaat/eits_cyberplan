"""Add organization_people link table."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = 'add_organization_people'
down_revision = 'add_tenant_divisions'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'organization_people',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False),
        sa.Column('person_asset_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('assets.id'), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default='now()'),
    )
    op.create_index('ix_org_people_tenant', 'organization_people', ['tenant_id'])
    op.create_index('ix_org_people_person', 'organization_people', ['person_asset_id'])
    op.create_unique_constraint('uq_org_person', 'organization_people', ['tenant_id', 'person_asset_id'])


def downgrade():
    op.drop_constraint('uq_org_person', 'organization_people', type_='unique')
    op.drop_index('ix_org_people_person', 'organization_people')
    op.drop_index('ix_org_people_tenant', 'organization_people')
    op.drop_table('organization_people')