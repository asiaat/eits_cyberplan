"""merge all heads

Revision ID: 47a801ddd3a5
Revises: 120e01d715df, add_asset_is_core_field, add_asset_relation_types_v1, add_evidence_file_stats, add_imr_requirement_profile_fields
Create Date: 2026-05-24 08:13:44.895154

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '47a801ddd3a5'
down_revision: Union[str, None] = ('120e01d715df', 'add_asset_is_core_field', 'add_asset_relation_types_v1', 'add_evidence_file_stats', 'add_imr_requirement_profile_fields')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass