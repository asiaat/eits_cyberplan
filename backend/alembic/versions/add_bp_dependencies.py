"""Create business_process_dependencies table.

Revision ID: add_bp_dependencies
Revises: v4_etl_compatibility
Create Date: 2026-05-20

Tracks process-to-process dependencies for E-ITS cascading
compliance tracking per bp_evidence.pdf requirements.
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'add_bp_dependencies'
down_revision: Union[str, None] = 'v4_etl_compatibility'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'business_process_dependencies',
        sa.Column('id', sa.UUID(), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('primary_process_id', sa.UUID(), nullable=False),
        sa.Column('depends_on_process_id', sa.UUID(), nullable=False),
        sa.Column('dependency_type', sa.String(length=50), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['tenant_id'], ['app_tenants.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['primary_process_id'], ['business_processes.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['depends_on_process_id'], ['business_processes.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('primary_process_id', 'depends_on_process_id', name='uq_bp_dependency_pair'),
    )
    op.create_index('ix_bp_dep_primary', 'business_process_dependencies', ['primary_process_id'], unique=False)
    op.create_index('ix_bp_dep_depends_on', 'business_process_dependencies', ['depends_on_process_id'], unique=False)
    op.create_index('ix_bp_dep_tenant_id', 'business_process_dependencies', ['tenant_id'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_bp_dep_tenant_id', 'business_process_dependencies', if_exists=True)
    op.drop_index('ix_bp_dep_depends_on', 'business_process_dependencies', if_exists=True)
    op.drop_index('ix_bp_dep_primary', 'business_process_dependencies', if_exists=True)
    op.drop_table('business_process_dependencies', if_exists=True)