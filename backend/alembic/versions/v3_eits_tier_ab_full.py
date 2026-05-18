"""E-ITS v2 full schema - Tier A/B tables and existing table extensions.

Revision ID: v3_eits_tier_ab_full
Revises: merge_eits_v2_base
Create Date: 2026-05-18

Adds:
- Tier A: catalog_versions (updated), eits_modules (updated), eits_catalog_measures,
  eits_threats, module_threats, damage_scenarios
- Tier B: asset_type_categories, security_profiles, damage_assessments,
  protection_need_summaries, asset_module_mappings, imr_items, risk_measure_links,
  damage_category_thresholds, process_module_assignments
- Existing table extensions: business_processes, assets, risks, evidence_links
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = 'v3_eits_tier_ab_full'
down_revision: Union[str, None] = 'mark_fix_audit_logs_applied'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # =============================================
    # TIER A: E-ITS ETALONTURBE KATALOOG
    # =============================================

    # --- 1. Update catalog_versions (already exists as eits_catalog_versions) ---
    # Add E-ITS v2 fields to the existing table
    op.add_column('eits_catalog_versions', sa.Column('year', sa.String(4), nullable=True))
    op.add_column('eits_catalog_versions', sa.Column('name', sa.String(100), nullable=True))
    op.add_column('eits_catalog_versions', sa.Column('is_active', sa.Boolean(), server_default='false'))
    op.add_column('eits_catalog_versions', sa.Column('released_at', sa.Date(), nullable=True))
    op.create_index('ix_eits_catalog_versions_year', 'eits_catalog_versions', ['year'], unique=False)
    op.create_index('ix_eits_catalog_versions_active', 'eits_catalog_versions', ['is_active'], unique=False)

    # --- 2. Update eits_modules (add module_group, rename/extend description) ---
    # The old eits_modules table already has: id, catalog_version_id, code, name, category, description, module_type, source_url
    # Add module_group field
    op.add_column('eits_modules', sa.Column('module_group', sa.String(10), nullable=True))
    op.create_index('ix_eits_modules_version', 'eits_modules', ['catalog_version_id'], unique=False)
    op.create_index('ix_eits_modules_group', 'eits_modules', ['module_group'], unique=False)

    # --- 3. eits_catalog_measures (new table - replaces extension of eits_measures) ---
    # This is the new E-ITS measures table with full PEARO support
    op.create_table(
        'eits_catalog_measures',
        sa.Column('id', sa.UUID(), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('module_id', sa.UUID(), nullable=False),
        sa.Column('code', sa.String(30), nullable=False),
        sa.Column('name', sa.Text(), nullable=False),
        sa.Column('measure_level', sa.String(10), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('responsible_role', sa.String(100), nullable=True),
        sa.ForeignKeyConstraint(['module_id'], ['eits_modules.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('module_id', 'code', name='uq_eits_catalog_measures_module_code'),
        sa.CheckConstraint("measure_level IN ('BASE', 'STANDARD', 'HIGH')", name='ck_measure_level'),
    )
    op.create_index('ix_eits_catalog_measures_module', 'eits_catalog_measures', ['module_id'], unique=False)
    op.create_index('ix_eits_catalog_measures_level', 'eits_catalog_measures', ['measure_level'], unique=False)

    # --- 4. eits_threats (new table) ---
    op.create_table(
        'eits_threats',
        sa.Column('id', sa.UUID(), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('version_id', sa.UUID(), nullable=False),
        sa.Column('code', sa.String(30), nullable=False),
        sa.Column('category', sa.String(100), nullable=True),
        sa.Column('impact_area', sa.String(100), nullable=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['version_id'], ['eits_catalog_versions.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('version_id', 'code', name='uq_eits_threats_version_code'),
    )
    op.create_index('ix_eits_threats_version', 'eits_threats', ['version_id'], unique=False)

    # --- 5. module_threats (new table) ---
    op.create_table(
        'module_threats',
        sa.Column('id', sa.UUID(), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('module_id', sa.UUID(), nullable=False),
        sa.Column('threat_id', sa.UUID(), nullable=False),
        sa.Column('relevance_note', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['module_id'], ['eits_modules.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['threat_id'], ['eits_threats.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('module_id', 'threat_id', name='uq_module_threats'),
    )

    # --- 6. damage_scenarios (new table, pre-populated) ---
    op.create_table(
        'damage_scenarios',
        sa.Column('id', sa.UUID(), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('code', sa.String(10), nullable=False, unique=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
    )
    # Seed damage scenarios
    op.execute("""
        INSERT INTO damage_scenarios (code, name, description) VALUES
        ('KS1', 'Ôigusaktide, eeskirjade või lepingute rikkumine',
         'Seaduste, määruste, lepingute, andmekaitse-eeskirjade rikkumisest tulenev kahju'),
        ('KS2', 'Teabelise enesemääramisõiguse rikkumine',
         'Isikuandmete töötlemise rikkumisest ja privaatsuse kaost tulenev kahju'),
        ('KS3', 'Füüsiline kahju',
         'Inimeste elule, tervisele ja keskkonnale tekitatav kahju'),
        ('KS4', 'Ülesannete täitmise võime kahjustamine',
         'Organisatsiooni protsesside ja ülesannete täitmise häirumisest tulenev kahju'),
        ('KS5', 'Negatiivsed sisemised või välised toimed',
         'Maine kahjustamine, usaldusväärsuse langus sihtrühmade, töötajate ja partnerite silmis'),
        ('KS6', 'Rahalised tagajärjed',
         'Otsesed ja kaudsed rahalised kahjud, kahjunõuded, trahvid')
        ON CONFLICT (code) DO NOTHING
    """)

    # =============================================
    # TIER B: TENANDIPÕHISED TÄIENDUSED
    # =============================================

    # --- 7. asset_type_categories (new table) ---
    op.create_table(
        'asset_type_categories',
        sa.Column('id', sa.UUID(), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('code', sa.String(5), nullable=False, unique=True),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
    )
    # Seed asset type categories
    op.execute("""
        INSERT INTO asset_type_categories (code, name, description) VALUES
        ('T', 'Taristu', 'Hooned, ruumid, tehnosüsteemid'),
        ('V', 'Võrgukomponendid', 'LAN, WAN, WLAN, VPN, tulemüür, ruuterid'),
        ('I', 'IT-süsteemid', 'Serverid, klientarvutid, sülearvutid, mobiilseadmed, printerid'),
        ('R', 'Rakendused', 'Tarkvararakendused, andmebaasid, veebiteenused, e-post'),
        ('A', 'Tööstusautomaatika', 'PLC, SCADA, ICS kontrollerid')
        ON CONFLICT (code) DO NOTHING
    """)

    # --- 8. security_profiles (new table) ---
    op.create_table(
        'security_profiles',
        sa.Column('id', sa.UUID(), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('catalog_version_id', sa.UUID(), nullable=True),
        sa.Column('security_approach', sa.String(20), nullable=False, server_default='BASIC'),
        sa.Column('approved_by', sa.UUID(), nullable=True),
        sa.Column('approved_at', sa.DateTime(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['tenant_id'], ['app_tenants.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['catalog_version_id'], ['eits_catalog_versions.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['approved_by'], ['local_users.id'], ondelete='SET NULL'),
        sa.UniqueConstraint('tenant_id', 'catalog_version_id', name='uq_security_profile_tenant_version'),
        sa.CheckConstraint("security_approach IN ('BASIC', 'STANDARD', 'CORE')", name='ck_security_approach'),
    )
    op.create_index('ix_security_profiles_tenant', 'security_profiles', ['tenant_id'], unique=False)

    # --- 9. Extend business_processes (add process_type, priority) ---
    op.add_column('business_processes', sa.Column('process_type', sa.String(20), server_default='OPERATIVE'))
    op.add_column('business_processes', sa.Column('priority', sa.Integer(), server_default='2'))
    op.execute("ALTER TABLE business_processes ADD CONSTRAINT ck_bp_process_type CHECK (process_type IN ('OPERATIVE', 'SUPPORTING'))")
    op.execute("ALTER TABLE business_processes ADD CONSTRAINT ck_bp_priority CHECK (priority BETWEEN 1 AND 3)")

    # --- 10. damage_assessments (new table) ---
    op.create_table(
        'damage_assessments',
        sa.Column('id', sa.UUID(), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('business_process_id', sa.UUID(), nullable=False),
        sa.Column('damage_scenario_id', sa.UUID(), nullable=False),
        sa.Column('availability_impact', sa.Integer(), server_default='0'),
        sa.Column('confidentiality_impact', sa.Integer(), server_default='0'),
        sa.Column('integrity_impact', sa.Integer(), server_default='0'),
        sa.Column('damage_category', sa.Integer(), nullable=True),
        sa.Column('justification', sa.Text(), nullable=True),
        sa.Column('assessed_by', sa.UUID(), nullable=True),
        sa.Column('assessed_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['tenant_id'], ['app_tenants.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['business_process_id'], ['business_processes.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['damage_scenario_id'], ['damage_scenarios.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['assessed_by'], ['local_users.id'], ondelete='SET NULL'),
        sa.UniqueConstraint('tenant_id', 'business_process_id', 'damage_scenario_id', name='uq_damage_assessment'),
        sa.CheckConstraint('availability_impact BETWEEN 0 AND 3', name='ck_availability_impact'),
        sa.CheckConstraint('confidentiality_impact BETWEEN 0 AND 3', name='ck_confidentiality_impact'),
        sa.CheckConstraint('integrity_impact BETWEEN 0 AND 3', name='ck_integrity_impact'),
    )
    op.create_index('ix_damage_assessments_tenant', 'damage_assessments', ['tenant_id'], unique=False)
    op.create_index('ix_damage_assessments_process', 'damage_assessments', ['business_process_id'], unique=False)

    # Update damage_category from triggers or via application logic
    op.execute("""
        CREATE OR REPLACE FUNCTION update_damage_category() RETURNS TRIGGER AS $$
        BEGIN
            NEW.damage_category := GREATEST(
                COALESCE(NEW.availability_impact, 0),
                COALESCE(NEW.confidentiality_impact, 0),
                COALESCE(NEW.integrity_impact, 0)
            );
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)
    op.execute("""
        DROP TRIGGER IF EXISTS trg_damage_assessment_damage_category ON damage_assessments;
        CREATE TRIGGER trg_damage_assessment_damage_category
        BEFORE INSERT OR UPDATE ON damage_assessments
        FOR EACH ROW EXECUTE FUNCTION update_damage_category();
    """)

    # --- 11. protection_need_summaries (new table) ---
    op.create_table(
        'protection_need_summaries',
        sa.Column('id', sa.UUID(), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('business_process_id', sa.UUID(), nullable=False),
        sa.Column('protection_need', sa.String(20), nullable=False, server_default='NORMAL'),
        sa.Column('confidentiality_need', sa.String(20), server_default='NORMAL'),
        sa.Column('integrity_need', sa.String(20), server_default='NORMAL'),
        sa.Column('availability_need', sa.String(20), server_default='NORMAL'),
        sa.Column('justification', sa.Text(), nullable=True),
        sa.Column('approved_by', sa.UUID(), nullable=True),
        sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['tenant_id'], ['app_tenants.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['business_process_id'], ['business_processes.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['approved_by'], ['local_users.id'], ondelete='SET NULL'),
        sa.UniqueConstraint('tenant_id', 'business_process_id', name='uq_protection_need_summary'),
        sa.CheckConstraint("protection_need IN ('NORMAL', 'HIGH', 'VERY_HIGH')", name='ck_protection_need'),
        sa.CheckConstraint("confidentiality_need IN ('NORMAL', 'HIGH', 'VERY_HIGH')", name='ck_confidentiality_need'),
        sa.CheckConstraint("integrity_need IN ('NORMAL', 'HIGH', 'VERY_HIGH')", name='ck_integrity_need'),
        sa.CheckConstraint("availability_need IN ('NORMAL', 'HIGH', 'VERY_HIGH')", name='ck_availability_need'),
    )
    op.create_index('ix_protection_needs_tenant', 'protection_need_summaries', ['tenant_id'], unique=False)

    # --- 12. Extend assets (E-ITS fields) ---
    op.add_column('assets', sa.Column('asset_index', sa.String(10), nullable=True))
    op.add_column('assets', sa.Column('asset_category', sa.String(5), nullable=True))
    op.add_column('assets', sa.Column('location', sa.String(255), nullable=True))
    op.add_column('assets', sa.Column('quantity', sa.Integer(), server_default='1'))
    op.add_column('assets', sa.Column('group_name', sa.String(255), nullable=True))
    op.add_column('assets', sa.Column('is_grouped', sa.Boolean(), server_default='false'))
    op.add_column('assets', sa.Column('protection_need', sa.String(20), server_default='NORMAL'))
    op.add_column('assets', sa.Column('protection_need_justification', sa.Text(), nullable=True))
    op.add_column('assets', sa.Column('protection_source_process_ids', sa.ARRAY(sa.UUID()), nullable=True))
    op.execute("ALTER TABLE assets ADD CONSTRAINT ck_asset_protection_need CHECK (protection_need IN ('NORMAL', 'HIGH', 'VERY_HIGH'))")
    op.execute("ALTER TABLE assets ADD CONSTRAINT ck_asset_quantity CHECK (quantity >= 1)")
    op.create_index('ix_assets_category', 'assets', ['asset_category'], unique=False)
    op.create_index('ix_assets_protection', 'assets', ['tenant_id', 'protection_need'], unique=False)

    # --- 13. asset_module_mappings (new table - E-ITS modelleerimine) ---
    op.create_table(
        'asset_module_mappings',
        sa.Column('id', sa.UUID(), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('asset_id', sa.UUID(), nullable=False),
        sa.Column('module_id', sa.UUID(), nullable=False),
        sa.Column('justification', sa.Text(), nullable=True),
        sa.Column('modeled_by', sa.UUID(), nullable=True),
        sa.Column('modeled_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['tenant_id'], ['app_tenants.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['asset_id'], ['assets.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['module_id'], ['eits_modules.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['modeled_by'], ['local_users.id'], ondelete='SET NULL'),
        sa.UniqueConstraint('tenant_id', 'asset_id', 'module_id', name='uq_asset_module_mapping'),
    )
    op.create_index('ix_asset_module_mappings_tenant', 'asset_module_mappings', ['tenant_id'], unique=False)
    op.create_index('ix_asset_module_mappings_asset', 'asset_module_mappings', ['asset_id'], unique=False)

    # --- 14. imr_items (new table - E-ITS IMR with PEARO) ---
    op.create_table(
        'imr_items',
        sa.Column('id', sa.UUID(), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('asset_module_mapping_id', sa.UUID(), nullable=True),
        sa.Column('measure_id', sa.UUID(), nullable=False),
        sa.Column('is_process_module_measure', sa.Boolean(), server_default='false'),
        sa.Column('pearo_status', sa.String(1), nullable=False, server_default='E'),
        sa.Column('implementation_description', sa.Text(), nullable=True),
        sa.Column('non_implementation_justification', sa.Text(), nullable=True),
        sa.Column('partial_scope_description', sa.Text(), nullable=True),
        sa.Column('responsible_user_id', sa.UUID(), nullable=True),
        sa.Column('due_date', sa.Date(), nullable=True),
        sa.Column('next_review_date', sa.Date(), nullable=True),
        sa.Column('priority', sa.String(5), server_default='P2'),
        sa.Column('risk_acceptance_approved_by', sa.UUID(), nullable=True),
        sa.Column('risk_acceptance_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('verification_method', sa.Text(), nullable=True),
        sa.Column('last_verified_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['tenant_id'], ['app_tenants.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['asset_module_mapping_id'], ['asset_module_mappings.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['measure_id'], ['eits_catalog_measures.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['responsible_user_id'], ['local_users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['risk_acceptance_approved_by'], ['local_users.id'], ondelete='SET NULL'),
        sa.CheckConstraint("pearo_status IN ('P', 'E', 'A', 'R', 'O')", name='ck_pearo_status'),
        sa.CheckConstraint("priority IN ('P1', 'P2', 'P3')", name='ck_imr_priority'),
    )
    op.create_index('ix_imr_items_tenant', 'imr_items', ['tenant_id'], unique=False)
    op.create_index('ix_imr_items_pearo', 'imr_items', ['tenant_id', 'pearo_status'], unique=False)
    op.create_index('ix_imr_items_due', 'imr_items', ['tenant_id', 'due_date'], unique=False)

    # --- 15. Extend risks (E-ITS risk fields) ---
    op.add_column('risks', sa.Column('threat_id', sa.UUID(), nullable=True))
    op.add_column('risks', sa.Column('asset_id', sa.UUID(), nullable=True))
    op.add_column('risks', sa.Column('business_process_id', sa.UUID(), nullable=True))
    op.add_column('risks', sa.Column('likelihood_score', sa.Integer(), nullable=True))
    op.add_column('risks', sa.Column('impact_score', sa.Integer(), nullable=True))
    op.execute("ALTER TABLE risks ADD COLUMN risk_score INTEGER GENERATED ALWAYS AS (likelihood_score * impact_score) STORED")
    op.add_column('risks', sa.Column('risk_rating', sa.String(20), nullable=True))
    op.add_column('risks', sa.Column('treatment_type', sa.String(30), nullable=True))
    op.add_column('risks', sa.Column('residual_risk_level', sa.String(20), nullable=True))
    op.add_column('risks', sa.Column('accepted_by', sa.UUID(), nullable=True))
    op.add_column('risks', sa.Column('accepted_at', sa.DateTime(timezone=True), nullable=True))
    op.execute("ALTER TABLE risks ADD CONSTRAINT ck_likelihood_score CHECK (likelihood_score BETWEEN 0 AND 3)")
    op.execute("ALTER TABLE risks ADD CONSTRAINT ck_impact_score CHECK (impact_score BETWEEN 0 AND 3)")
    op.execute("ALTER TABLE risks ADD CONSTRAINT ck_treatment_type CHECK (treatment_type IN ('MITIGATE', 'ACCEPT', 'TRANSFER', 'AVOID'))")
    op.create_index('ix_risks_threat', 'risks', ['threat_id'], unique=False)
    op.create_index('ix_risks_asset', 'risks', ['asset_id'], unique=False)
    op.create_index('ix_risks_business_process', 'risks', ['business_process_id'], unique=False)

    # --- 16. risk_measure_links (new table) ---
    op.create_table(
        'risk_measure_links',
        sa.Column('id', sa.UUID(), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('risk_id', sa.UUID(), nullable=False),
        sa.Column('imr_item_id', sa.UUID(), nullable=True),
        sa.Column('measure_id', sa.UUID(), nullable=True),
        sa.Column('custom_measure_name', sa.String(255), nullable=True),
        sa.Column('custom_measure_description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['tenant_id'], ['app_tenants.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['risk_id'], ['risks.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['imr_item_id'], ['imr_items.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['measure_id'], ['eits_catalog_measures.id'], ondelete='SET NULL'),
    )
    op.create_index('ix_risk_measure_links_risk', 'risk_measure_links', ['risk_id'], unique=False)

    # --- 17. damage_category_thresholds (new table) ---
    op.create_table(
        'damage_category_thresholds',
        sa.Column('id', sa.UUID(), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('damage_scenario_id', sa.UUID(), nullable=False),
        sa.Column('negligible_description', sa.Text(), nullable=True),
        sa.Column('limited_description', sa.Text(), nullable=True),
        sa.Column('serious_description', sa.Text(), nullable=True),
        sa.Column('catastrophic_description', sa.Text(), nullable=True),
        sa.Column('approved_by', sa.UUID(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['tenant_id'], ['app_tenants.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['damage_scenario_id'], ['damage_scenarios.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['approved_by'], ['local_users.id'], ondelete='SET NULL'),
        sa.UniqueConstraint('tenant_id', 'damage_scenario_id', name='uq_damage_threshold'),
    )
    op.create_index('ix_damage_thresholds_tenant', 'damage_category_thresholds', ['tenant_id'], unique=False)

    # --- 18. process_module_assignments (new table) ---
    op.create_table(
        'process_module_assignments',
        sa.Column('id', sa.UUID(), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('module_id', sa.UUID(), nullable=False),
        sa.Column('is_applicable', sa.Boolean(), server_default='true'),
        sa.Column('non_applicability_justification', sa.Text(), nullable=True),
        sa.Column('assigned_by', sa.UUID(), nullable=True),
        sa.Column('assigned_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['tenant_id'], ['app_tenants.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['module_id'], ['eits_modules.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['assigned_by'], ['local_users.id'], ondelete='SET NULL'),
        sa.UniqueConstraint('tenant_id', 'module_id', name='uq_process_module_assignment'),
    )
    op.create_index('ix_process_module_assignments_tenant', 'process_module_assignments', ['tenant_id'], unique=False)

    # --- 19. Extend evidence_links (add link_type) ---
    op.add_column('evidence_links', sa.Column('link_type', sa.String(50), server_default='general'))
    op.create_index('ix_evidence_links_type', 'evidence_links', ['link_type'], unique=False)

    # --- 20. Create views ---
    op.execute("""
        CREATE OR REPLACE VIEW v_imr_summary AS
        SELECT
            i.tenant_id,
            i.pearo_status,
            cm.measure_level,
            COUNT(*) AS measure_count,
            COUNT(*) FILTER (WHERE i.due_date < CURRENT_DATE AND i.pearo_status IN ('E','O')) AS overdue_count
        FROM imr_items i
        JOIN eits_catalog_measures cm ON cm.id = i.measure_id
        GROUP BY i.tenant_id, i.pearo_status, cm.measure_level
    """)

    op.execute("""
        CREATE OR REPLACE VIEW v_asset_protection_overview AS
        SELECT
            a.tenant_id,
            a.id AS asset_id,
            a.asset_index,
            a.name AS asset_name,
            a.asset_category,
            a.protection_need,
            COUNT(DISTINCT amm.module_id) AS mapped_module_count,
            COUNT(DISTINCT i.id) AS imr_item_count,
            COUNT(DISTINCT i.id) FILTER (WHERE i.pearo_status = 'R') AS implemented_count,
            COUNT(DISTINCT i.id) FILTER (WHERE i.pearo_status = 'E') AS not_implemented_count
        FROM assets a
        LEFT JOIN asset_module_mappings amm ON amm.asset_id = a.id
        LEFT JOIN imr_items i ON i.asset_module_mapping_id = amm.id
        GROUP BY a.tenant_id, a.id, a.asset_index, a.name, a.asset_category, a.protection_need
    """)

    op.execute("""
        CREATE OR REPLACE VIEW v_risk_matrix AS
        SELECT
            r.tenant_id,
            r.impact_score,
            r.likelihood_score,
            COUNT(*) AS risk_count,
            ARRAY_AGG(r.title) AS risk_titles
        FROM risks r
        WHERE r.impact_score IS NOT NULL AND r.likelihood_score IS NOT NULL
        GROUP BY r.tenant_id, r.impact_score, r.likelihood_score
    """)


def downgrade() -> None:
    # Drop views
    op.execute("DROP VIEW IF EXISTS v_risk_matrix")
    op.execute("DROP VIEW IF EXISTS v_asset_protection_overview")
    op.execute("DROP VIEW IF EXISTS v_imr_summary")

    # Drop Tier B tables
    op.drop_table('process_module_assignments')
    op.drop_table('damage_category_thresholds')
    op.drop_table('risk_measure_links')
    op.drop_table('imr_items')
    op.drop_table('asset_module_mappings')
    op.drop_table('protection_need_summaries')
    op.drop_table('damage_assessments')
    op.drop_table('security_profiles')
    op.drop_table('asset_type_categories')
    op.drop_table('damage_scenarios')

    # Drop Tier A tables
    op.drop_table('module_threats')
    op.drop_table('eits_threats')
    op.drop_table('eits_catalog_measures')

    # Remove business_processes columns
    op.drop_column('business_processes', 'priority')
    op.drop_column('business_processes', 'process_type')

    # Remove assets columns
    op.drop_column('assets', 'protection_source_process_ids')
    op.drop_column('assets', 'protection_need_justification')
    op.drop_column('assets', 'protection_need')
    op.drop_column('assets', 'is_grouped')
    op.drop_column('assets', 'group_name')
    op.drop_column('assets', 'quantity')
    op.drop_column('assets', 'location')
    op.drop_column('assets', 'asset_category')
    op.drop_column('assets', 'asset_index')

    # Remove risks columns
    op.drop_column('risks', 'accepted_at')
    op.drop_column('risks', 'accepted_by')
    op.drop_column('risks', 'residual_risk_level')
    op.drop_column('risks', 'treatment_type')
    op.drop_column('risks', 'risk_rating')
    op.drop_column('risks', 'risk_score')
    op.drop_column('risks', 'impact_score')
    op.drop_column('risks', 'likelihood_score')
    op.drop_column('risks', 'business_process_id')
    op.drop_column('risks', 'asset_id')
    op.drop_column('risks', 'threat_id')

    # Remove evidence_links columns
    op.drop_column('evidence_links', 'link_type')

    # Remove eits_catalog_versions columns
    op.drop_index('ix_eits_catalog_versions_active', 'eits_catalog_versions')
    op.drop_index('ix_eits_catalog_versions_year', 'eits_catalog_versions')
    op.drop_column('eits_catalog_versions', 'released_at')
    op.drop_column('eits_catalog_versions', 'is_active')
    op.drop_column('eits_catalog_versions', 'name')
    op.drop_column('eits_catalog_versions', 'year')

    # Remove eits_modules columns
    op.drop_index('ix_eits_modules_group', 'eits_modules')
    op.drop_index('ix_eits_modules_version', 'eits_modules')
    op.drop_column('eits_modules', 'module_group')