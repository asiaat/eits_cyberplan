"""Add bp_module_mappings and imr_items tables for scope modeling.

Revision ID: add_scope_modeling
Revises: cleanup_pm_constraints
Create Date: 2026-05-21
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = 'add_scope_modeling'
down_revision: Union[str, None] = 'cleanup_pm_constraints'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'bp_module_mappings',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('app_tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('business_process_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('business_processes.id', ondelete='CASCADE'), nullable=False),
        sa.Column('module_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('eits_modules.id', ondelete='CASCADE'), nullable=False),
        sa.Column('justification', sa.Text(), nullable=True),
        sa.Column('modeled_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('local_users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('modeled_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.UniqueConstraint('tenant_id', 'business_process_id', 'module_id', name='uq_bp_module_mapping'),
    )
    op.create_index('ix_bp_module_mappings_lookup', 'bp_module_mappings', ['business_process_id'])

    # imr_items may already exist from v3_eits_tier_ab_full — add bp_module_mapping_id if missing
    op.execute("ALTER TABLE imr_items ADD COLUMN IF NOT EXISTS bp_module_mapping_id UUID")
    op.execute("ALTER TABLE imr_items ADD CONSTRAINT fk_imr_items_bp_mapping FOREIGN KEY (bp_module_mapping_id) REFERENCES bp_module_mappings(id) ON DELETE CASCADE")
    op.execute("CREATE INDEX IF NOT EXISTS ix_imr_items_bp_mapping ON imr_items (bp_module_mapping_id)")


def downgrade() -> None:
    op.drop_table('imr_items')
    op.drop_table('bp_module_mappings')
