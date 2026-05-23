"""Add asset relation types and circular dependency trigger.

Revision ID: add_asset_relation_types_v1
Revises:
Create Date: 2026-05-23 15:40:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'add_asset_relation_types_v1'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create asset_relation_types table
    op.create_table(
        'asset_relation_types',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('code', sa.String(50), nullable=False, unique=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('source_types', sa.String(500)),  # JSON array of allowed source asset types, e.g. '["APP","SYS"]'
        sa.Column('target_types', sa.String(500)),  # JSON array of allowed target asset types
        sa.Column('bidirectional', sa.Boolean, default=False),
        sa.Column('strength', sa.String(20), default='weak'),  # 'strong' or 'weak'
        sa.Column('created_at', sa.DateTime, server_default=sa.text('now()')),
    )
    op.create_index('ix_asset_relation_types_code', 'asset_relation_types', ['code'])

    # Insert standard relation types
    op.execute("""
        INSERT INTO asset_relation_types (code, name, description, source_types, target_types, bidirectional, strength) VALUES
        ('runs_on', 'Runs On', 'Asset runs on or is hosted by another asset', '["APP","SYS"]', '["SYS","INF"]', false, 'strong'),
        ('located_in', 'Located In', 'Asset is physically located in another asset', '["SYS","INF"]', '["INF"]', false, 'strong'),
        ('connected_to', 'Connected To', 'Asset is connected to another asset via network', '["SYS","NET"]', '["NET"]', false, 'weak'),
        ('stores', 'Stores', 'Asset stores or contains data from another asset', '["APP","SYS"]', '["DATA"]', false, 'weak'),
        ('uses_service', 'Uses Service', 'Asset uses or depends on a service', '["APP","SYS","NET"]', '["SVC","APP"]', false, 'weak'),
        ('depends_on', 'Depends On', 'Generic dependency relationship', '["APP","SYS","NET","INF","DATA"]', '["APP","SYS","NET","INF","DATA","SVC"]', true, 'weak'),
        ('supports', 'Supports', 'Asset supports or enables another asset', '["APP","SYS","NET"]', '["APP","SYS"]', false, 'weak'),
        ('contains', 'Contains', 'Asset contains other assets (grouping)', '["INF","NET"]', '["SYS","INF","NET"]', true, 'strong');
    """)

    # Add new columns to asset_relations
    op.add_column('asset_relations', sa.Column('relation_type_code', sa.String(50), sa.ForeignKey('asset_relation_types.code'), nullable=True))
    op.add_column('asset_relations', sa.Column('bidirectional', sa.Boolean, default=False))
    op.add_column('asset_relations', sa.Column('strength', sa.String(20), default='weak'))
    op.add_column('asset_relations', sa.Column('created_at', sa.DateTime, server_default=sa.text('now()')))

    # Migrate existing relation_type values to new codes
    op.execute("""
        UPDATE asset_relations SET relation_type_code = relation_type WHERE relation_type IS NOT NULL
    """)

    # Create function to check circular dependency
    op.execute("""
        CREATE OR REPLACE FUNCTION check_asset_relation_circular()
        RETURNS TRIGGER AS $$
        DECLARE
            cycle_detected boolean;
        BEGIN
            -- Check if adding this relation would create a cycle
            -- A cycle exists if target_asset can already reach source_asset
            WITH RECURSIVE dependency_chain AS (
                -- Start from the target asset
                SELECT ar.target_asset_id, ar.source_asset_id, ARRAY[ar.target_asset_id] as path, 1 as depth
                FROM asset_relations ar
                WHERE ar.source_asset_id = NEW.target_asset_id
                
                UNION ALL
                
                -- Follow the chain
                SELECT ar.target_asset_id, ar.source_asset_id, dc.path || ar.target_asset_id, dc.depth + 1
                FROM asset_relations ar
                JOIN dependency_chain dc ON ar.source_asset_id = dc.target_asset_id
                WHERE NOT ar.target_asset_id = ANY(dc.path) AND dc.depth < 100
            )
            SELECT EXISTS (
                SELECT 1 FROM dependency_chain WHERE target_asset_id = NEW.source_asset_id
            ) INTO cycle_detected;

            IF cycle_detected THEN
                RAISE EXCEPTION 'Circular dependency detected: adding this relation would create a cycle';
            END IF;

            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """);

    # Create trigger for insert
    op.execute("""
        CREATE TRIGGER check_asset_relation_circular_insert
        BEFORE INSERT ON asset_relations
        FOR EACH ROW
        EXECUTE FUNCTION check_asset_relation_circular();
    """);

    # Create trigger for update (if target changes)
    op.execute("""
        CREATE TRIGGER check_asset_relation_circular_update
        BEFORE UPDATE OF target_asset_id ON asset_relations
        FOR EACH ROW
        EXECUTE FUNCTION check_asset_relation_circular();
    """);

    # Create view for protection inheritance calculation
    op.execute("""
        CREATE OR REPLACE VIEW v_asset_protection_inheritance AS
        WITH RECURSIVE asset_propagation AS (
            -- Base case: all assets with their baseline values
            SELECT 
                a.id,
                a.tenant_id,
                a.name,
                a.asset_type,
                a.confidentiality_need as baseline_c,
                a.integrity_need as baseline_i,
                a.availability_need as baseline_a,
                a.confidentiality_need as inherited_c,
                a.integrity_need as inherited_i,
                a.availability_need as inherited_a,
                ARRAY[a.id] as propagation_path,
                0 as propagation_depth,
                false as has_inherited_needs
            FROM assets a
            
            UNION ALL
            
            -- For each asset, calculate inherited needs from upstream (assets it depends on)
            SELECT 
                a.id,
                a.tenant_id,
                a.name,
                a.asset_type,
                a.confidentiality_need as baseline_c,
                a.integrity_need as baseline_i,
                a.availability_need as baseline_a,
                GREATEST(
                    a.confidentiality_need,
                    COALESCE(ap.inherited_c, a.confidentiality_need)
                ) as inherited_c,
                GREATEST(
                    a.integrity_need,
                    COALESCE(ap.inherited_i, a.integrity_need)
                ) as inherited_i,
                GREATEST(
                    a.availability_need,
                    COALESCE(ap.inherited_a, a.availability_need)
                ) as inherited_a,
                ap.propagation_path || a.id,
                ap.propagation_depth + 1,
                CASE WHEN ap.propagation_depth >= 0 THEN true ELSE false END
            FROM assets a
            JOIN asset_relations ar ON ar.target_asset_id = a.id
            LEFT JOIN asset_propagation ap ON ap.id = ar.source_asset_id
            WHERE NOT a.id = ANY(ap.propagation_path)
            AND ap.propagation_depth < 50
        )
        SELECT DISTINCT ON (id)
            id,
            tenant_id,
            name,
            asset_type,
            baseline_c,
            baseline_i,
            baseline_a,
            inherited_c,
            inherited_i,
            inherited_a,
            propagation_path,
            propagation_depth,
            has_inherited_needs,
            CASE 
                WHEN inherited_c != baseline_c OR inherited_i != baseline_i OR inherited_a != baseline_a 
                THEN true 
                ELSE false 
            END as needs_inherited
        FROM asset_propagation
        ORDER BY id, propagation_depth DESC;
    """);


def downgrade() -> None:
    op.execute("DROP VIEW IF EXISTS v_asset_protection_inheritance")
    op.execute("DROP TRIGGER IF EXISTS check_asset_relation_circular_update ON asset_relations")
    op.execute("DROP TRIGGER IF EXISTS check_asset_relation_circular_insert ON asset_relations")
    op.execute("DROP FUNCTION IF EXISTS check_asset_relation_circular()")
    op.drop_column('asset_relations', 'created_at')
    op.drop_column('asset_relations', 'strength')
    op.drop_column('asset_relations', 'bidirectional')
    op.drop_column('asset_relations', 'relation_type_code')
    op.drop_index('ix_asset_relation_types_code', 'asset_relation_types')
    op.drop_table('asset_relation_types')