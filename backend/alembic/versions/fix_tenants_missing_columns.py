"""Add missing columns to tenants table that exist in the Tenant model.

Revision ID: fix_tenants_missing_columns
Revises: 15dd342acd17
Create Date: 2026-06-06

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = 'fix_tenants_missing_columns'
down_revision: Union[str, Sequence[str], None] = '15dd342acd17'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('tenants', sa.Column('legal_form', sa.String(50), nullable=True))
    op.add_column('tenants', sa.Column('registration_date', sa.Date(), nullable=True))
    op.add_column('tenants', sa.Column('status', sa.String(50), nullable=True))
    op.add_column('tenants', sa.Column('registered_address', sa.Text(), nullable=True))
    op.add_column('tenants', sa.Column('contact_address', sa.Text(), nullable=True))
    op.add_column('tenants', sa.Column('phone', sa.String(50), nullable=True))
    op.add_column('tenants', sa.Column('email', sa.String(255), nullable=True))
    op.add_column('tenants', sa.Column('website', sa.String(255), nullable=True))
    op.add_column('tenants', sa.Column('share_capital', sa.Numeric(15, 2), nullable=True))
    op.add_column('tenants', sa.Column('nace_codes', sa.JSON(), nullable=True))
    op.add_column('tenants', sa.Column('company_type', sa.String(20), nullable=True))
    op.add_column('tenants', sa.Column('parent_company_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key('fk_tenants_parent_company', 'tenants', 'tenants', ['parent_company_id'], ['id'])


def downgrade() -> None:
    op.drop_constraint('fk_tenants_parent_company', 'tenants', type_='foreignkey')
    op.drop_column('tenants', 'parent_company_id')
    op.drop_column('tenants', 'company_type')
    op.drop_column('tenants', 'nace_codes')
    op.drop_column('tenants', 'share_capital')
    op.drop_column('tenants', 'website')
    op.drop_column('tenants', 'email')
    op.drop_column('tenants', 'phone')
    op.drop_column('tenants', 'contact_address')
    op.drop_column('tenants', 'registered_address')
    op.drop_column('tenants', 'status')
    op.drop_column('tenants', 'registration_date')
    op.drop_column('tenants', 'legal_form')
