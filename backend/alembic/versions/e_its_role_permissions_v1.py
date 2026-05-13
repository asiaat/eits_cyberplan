"""Create e_its_role_permissions table and migrate data.

Revision ID: e_its_role_permissions_v1
Revises: v2_iam_initial
Create Date: 2026-05-13
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision = 'e_its_role_permissions_v1'
down_revision = 'v2_iam_initial'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create the new e_its_role_permissions table with UUID for role_id
    op.create_table(
        'e_its_role_permissions',
        sa.Column('role_id', UUID(as_uuid=True), nullable=False),
        sa.Column('permission_id', sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(['role_id'], ['e_its_roles.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['permission_id'], ['permissions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('role_id', 'permission_id')
    )
    
    # Migrate existing role_permissions data to e_its_role_permissions
    # Only migrate for roles that exist in e_its_roles table (Infoturbejuht, IT-talitus, Juhtkond)
    op.execute("""
        INSERT INTO e_its_role_permissions (role_id, permission_id)
        SELECT rp.role_id::UUID, rp.permission_id
        FROM role_permissions rp
        INNER JOIN e_its_roles er ON rp.role_id = er.id::TEXT
        ON CONFLICT DO NOTHING
    """)


def downgrade() -> None:
    op.drop_table('e_its_role_permissions')