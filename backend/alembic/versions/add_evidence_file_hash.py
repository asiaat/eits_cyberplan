"""Add file_hash to evidences table for duplicate detection.

Revision ID: add_evidence_file_hash
Revises: add_bp_dependencies
Create Date: 2026-05-20

Adds file_hash column to enable SHA-256 based duplicate detection
when uploading evidence files.
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'add_evidence_file_hash'
down_revision: Union[str, None] = '117cf82799ad'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'evidences',
        sa.Column('file_hash', sa.String(length=64), nullable=True, index=True)
    )


def downgrade() -> None:
    op.drop_column('evidences', 'file_hash')