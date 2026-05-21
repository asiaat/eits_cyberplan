"""Create turbeviis_selections table for mode of protection.

Revision ID: add_turbeviis_selections
Revises: add_evidence_file_hash
Create Date: 2026-05-20

Creates table to store organization's selected turbeviis (protection mode)
with linked evidence document supporting the selection.
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'add_turbeviis_selections'
down_revision: Union[str, None] = 'add_evidence_file_hash'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'turbeviis_selections',
        sa.Column('id', sa.UUID(), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('catalog_version_id', sa.UUID(), nullable=True),
        sa.Column('security_approach', sa.String(length=20), nullable=False, default='BASIC'),
        sa.Column('evidence_id', sa.UUID(), nullable=True),
        sa.Column('approved_by', sa.UUID(), nullable=True),
        sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['tenant_id'], ['app_tenants.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['catalog_version_id'], ['eits_catalog_versions.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['evidence_id'], ['evidences.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['approved_by'], ['local_users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('tenant_id', 'catalog_version_id', name='uq_turbeviis_tenant_catalog'),
        sa.UniqueConstraint('tenant_id', 'is_active', name='uq_turbeviis_tenant_active'),
    )
    op.create_index('ix_turbeviis_tenant_id', 'turbeviis_selections', ['tenant_id'], unique=False)
    op.create_index('ix_turbeviis_catalog_version', 'turbeviis_selections', ['catalog_version_id'], unique=False)
    op.create_index('ix_turbeviis_security_approach', 'turbeviis_selections', ['security_approach'], unique=False)
    op.create_index('ix_turbeviis_is_active', 'turbeviis_selections', ['is_active'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_turbeviis_is_active', 'turbeviis_selections', if_exists=True)
    op.drop_index('ix_turbeviis_security_approach', 'turbeviis_selections', if_exists=True)
    op.drop_index('ix_turbeviis_catalog_version', 'turbeviis_selections', if_exists=True)
    op.drop_index('ix_turbeviis_tenant_id', 'turbeviis_selections', if_exists=True)
    op.drop_table('turbeviis_selections', if_exists=True)