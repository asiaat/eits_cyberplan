"""Add file size, mime type, download count to evidences.

Revision ID: add_evidence_file_stats
Revises: v4_etl_compatibility
Create Date: 2026-05-23

Adds file_size, mime_type, and download_count columns to enable
displaying file statistics on evidence cards.
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'add_evidence_file_stats'
down_revision: Union[str, None] = 'v4_etl_compatibility'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'evidences',
        sa.Column('file_size', sa.BigInteger(), nullable=True)
    )
    op.add_column(
        'evidences',
        sa.Column('mime_type', sa.String(length=100), nullable=True)
    )
    op.add_column(
        'evidences',
        sa.Column('download_count', sa.Integer(), nullable=False, server_default='0')
    )


def downgrade() -> None:
    op.drop_column('evidences', 'download_count')
    op.drop_column('evidences', 'mime_type')
    op.drop_column('evidences', 'file_size')
