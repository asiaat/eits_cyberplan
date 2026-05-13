"""Create persons and person_organizations tables.

Revision ID: create_persons_tables
Revises: 31420c85e7b9_merge_heads
Create Date: 2026-05-10 12:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = 'create_persons_tables'
down_revision: Union[str, None] = '59ba4f69c258'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'persons',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('national_id', sa.String(length=50), nullable=True, unique=True),
        sa.Column('first_name', sa.String(length=100), nullable=False),
        sa.Column('last_name', sa.String(length=100), nullable=False),
        sa.Column('date_of_birth', sa.Date(), nullable=True),
        sa.Column('email', sa.String(length=255), nullable=True),
        sa.Column('phone', sa.String(length=50), nullable=True),
        sa.Column('additional_info', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default='now()', nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default='now()', onupdate='now()', nullable=True),
    )
    op.create_index('ix_persons_national_id', 'persons', ['national_id'], unique=False)
    op.create_index('ix_persons_email', 'persons', ['email'], unique=False)

    op.create_table(
        'person_organizations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('person_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('persons.id'), nullable=False, index=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False, index=True),
        sa.Column('role', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default='now()', nullable=True),
    )
    op.create_index('ix_person_orgs_person', 'person_organizations', ['person_id'])
    op.create_index('ix_person_orgs_tenant', 'person_organizations', ['tenant_id'])
    op.create_unique_constraint('uq_person_tenant', 'person_organizations', ['person_id', 'tenant_id'])

    op.add_column('assets', sa.Column('person_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('persons.id'), nullable=True))
    op.create_index('ix_assets_person_id', 'assets', ['person_id'])


def downgrade() -> None:
    op.drop_index('ix_assets_person_id', table_name='assets')
    op.drop_column('assets', 'person_id')
    op.drop_constraint('uq_person_tenant', 'person_organizations', type_='unique')
    op.drop_index('ix_person_orgs_tenant', table_name='person_organizations')
    op.drop_index('ix_person_orgs_person', table_name='person_organizations')
    op.drop_table('person_organizations')
    op.drop_index('ix_persons_email', table_name='persons')
    op.drop_index('ix_persons_national_id', table_name='persons')
    op.drop_table('persons')
