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

    op.create_table(
        'imr_items',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('app_tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('asset_module_mapping_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('asset_module_mappings.id', ondelete='CASCADE'), nullable=True),
        sa.Column('bp_module_mapping_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('bp_module_mappings.id', ondelete='CASCADE'), nullable=True),
        sa.Column('measure_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('eits_catalog_measures.id', ondelete='CASCADE'), nullable=False),
        sa.Column('is_process_module_measure', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('pearo_status', sa.String(1), nullable=False, server_default='E'),
        sa.Column('implementation_description', sa.Text(), nullable=True),
        sa.Column('non_implementation_justification', sa.Text(), nullable=True),
        sa.Column('partial_scope_description', sa.Text(), nullable=True),
        sa.Column('responsible_user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('local_users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('due_date', sa.Date(), nullable=True),
        sa.Column('next_review_date', sa.Date(), nullable=True),
        sa.Column('priority', sa.String(5), server_default='P2'),
        sa.Column('risk_acceptance_approved_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('local_users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('risk_acceptance_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('verification_method', sa.Text(), nullable=True),
        sa.Column('last_verified_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
    )
    op.create_index('ix_imr_items_tenant', 'imr_items', ['tenant_id'])
    op.create_index('ix_imr_items_pearo', 'imr_items', ['tenant_id', 'pearo_status'])
    op.create_index('ix_imr_items_due', 'imr_items', ['tenant_id', 'due_date'])
    op.create_index('ix_imr_items_bp_mapping', 'imr_items', ['bp_module_mapping_id'])


def downgrade() -> None:
    op.drop_table('imr_items')
    op.drop_table('bp_module_mappings')
