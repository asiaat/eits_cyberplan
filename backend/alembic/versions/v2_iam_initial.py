"""IAM v2 initial - Tier A/B tables."""
from alembic import op
import uuid
from sqlalchemy import text, Column, String, Boolean, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Session


revision = 'v2_iam_initial'
down_revision = 'add_person_fk_restrict'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Enable pgcrypto for UUID generation
    op.execute('CREATE EXTENSION IF NOT EXISTS "pgcrypto"')

    # === TIER A: Subscription Layer ===
    
    # 1. AppTenants - Subscription registry (if not exists)
    try:
        op.create_table(
            'app_tenants',
            Column('id', UUID(as_uuid=True), primary_key=True, default=text('gen_random_uuid()')),
            Column('name', String(255), nullable=False),
            Column('status', String(50), server_default='active'),
            Column('plan', String(50)),
            Column('created_at', DateTime(timezone=True), server_default=text('now()')),
        )
    except:
        pass  # Table may already exist
    
    # 2. GlobalUsers - Central identity
    try:
        op.create_table(
            'global_users',
            Column('id', UUID(as_uuid=True), primary_key=True, default=text('gen_random_uuid()')),
            Column('email', String(255), unique=True, nullable=False),
            Column('password_hash', String(255), nullable=False),
            Column('mfa_enabled', Boolean(), server_default='false'),
            Column('mfa_secret', String(255)),
            Column('created_at', DateTime(timezone=True), server_default=text('now()')),
        )
        op.create_index('ix_global_users_email', 'global_users', ['email'])
    except:
        pass
    
    # 3. TenantUsers - User to tenant mapping
    try:
        op.create_table(
            'tenant_users',
            Column('tenant_id', UUID(as_uuid=True), primary_key=True),
            Column('user_id', UUID(as_uuid=True), primary_key=True),
            Column('assigned_at', DateTime(timezone=True), server_default=text('now()')),
        )
        op.create_foreign_key(
            'fk_tenant_users_tenant', 'tenant_users', 'app_tenants',
            ['tenant_id'], ['id'], ondelete='CASCADE'
        )
        op.create_foreign_key(
            'fk_tenant_users_user', 'tenant_users', 'global_users',
            ['user_id'], ['id'], ondelete='CASCADE'
        )
    except:
        pass
    
    # === TIER B: Per-Tenant ===
    
    # 4. LocalUsers - Per-tenant user profile
    try:
        op.create_table(
            'local_users',
            Column('id', UUID(as_uuid=True), primary_key=True, default=text('gen_random_uuid()')),
            Column('global_user_id', UUID(as_uuid=True), nullable=False),
            Column('tenant_id', UUID(as_uuid=True), nullable=False),
            Column('full_name', String(255), nullable=False),
            Column('department', String(100)),
            Column('is_active', Boolean(), server_default='true'),
            Column('created_at', DateTime(timezone=True), server_default=text('now()')),
        )
        op.create_unique_constraint('uq_local_user_global_tenant', 'local_users', ['global_user_id', 'tenant_id'])
        op.create_foreign_key(
            'fk_local_users_global_user', 'local_users', 'global_users',
            ['global_user_id'], ['id'], ondelete='CASCADE'
        )
        op.create_foreign_key(
            'fk_local_users_tenant', 'local_users', 'app_tenants',
            ['tenant_id'], ['id'], ondelete='CASCADE'
        )
    except:
        pass
    
    # 5. EITSRoles - Per-tenant E-ITS standard roles
    try:
        op.create_table(
            'e_its_roles',
            Column('id', UUID(as_uuid=True), primary_key=True, default=text('gen_random_uuid()')),
            Column('tenant_id', UUID(as_uuid=True), nullable=False),
            Column('role_name', String(100), nullable=False),
            Column('description', Text),
        )
        op.create_unique_constraint('uq_e_its_role_tenant', 'e_its_roles', ['tenant_id', 'role_name'])
        op.create_foreign_key(
            'fk_e_its_roles_tenant', 'e_its_roles', 'app_tenants',
            ['tenant_id'], ['id'], ondelete='CASCADE'
        )
    except:
        pass
    
    # 6. UserRoles - User role assignments
    try:
        op.create_table(
            'user_roles',
            Column('id', UUID(as_uuid=True), primary_key=True, default=text('gen_random_uuid()')),
            Column('user_id', UUID(as_uuid=True), nullable=False),
            Column('role_id', UUID(as_uuid=True), nullable=False),
            Column('granted_by', UUID(as_uuid=True)),
            Column('granted_at', DateTime(timezone=True), server_default=text('now()')),
        )
        op.create_foreign_key(
            'fk_user_roles_user', 'user_roles', 'local_users',
            ['user_id'], ['id'], ondelete='CASCADE'
        )
        op.create_foreign_key(
            'fk_user_roles_role', 'user_roles', 'e_its_roles',
            ['role_id'], ['id'], ondelete='CASCADE'
        )
    except:
        pass
    
    # === Add tenant_id to memberships for migration path (if not exists) ===
    try:
        result = op.get_bind().execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'memberships' AND column_name = 'tenant_id'"))
        if not result.fetch():
            op.add_column('memberships', Column('tenant_id', UUID(as_uuid=True), nullable=True))
    except:
        pass
    
    try:
        result = op.get_bind().execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'memberships' AND column_name = 'local_user_id'"))
        if not result.fetch():
            op.add_column('memberships', Column('local_user_id', UUID(as_uuid=True), nullable=True))
    except:
        pass
    
    # === Create default tenant and seed E-ITS roles ===
    try:
        result = op.get_bind().execute(text("SELECT id FROM app_tenants WHERE name = 'Default'"))
        if not result.fetch():
            default_tenant_id = str(uuid.uuid4())
            op.execute(f'''
                INSERT INTO app_tenants (id, name, status, plan)
                VALUES ('{default_tenant_id}', 'Default', 'active', 'enterprise');
            ''')
            
            # Seed E-ITS roles for default tenant
            op.execute(f'''
                INSERT INTO e_its_roles (id, tenant_id, role_name, description) VALUES 
                    (gen_random_uuid(), '{default_tenant_id}', 'infoturbejuht', 'Information Security Officer'),
                    (gen_random_uuid(), '{default_tenant_id}', 'it_talitus', 'IT Department'),
                    (gen_random_uuid(), '{default_tenant_id}', 'juhtkond', 'Management Board');
            ''')
    except:
        pass
    
    # === Drop FK on audit_logs.actor_user_id (to allow local_user ids) ===
    try:
        op.execute('ALTER TABLE audit_logs DROP CONSTRAINT IF EXISTS audit_logs_actor_user_id_fkey')
    except:
        pass
    
    # === Create audit trigger function (disabled for now - needs proper implementation) ===
    # TODO: Re-enable after fixing FK relationship between user_roles and audit_logs
    # try:
    #     op.execute('''
    #         CREATE OR REPLACE FUNCTION audit_user_roles_trigger_func()
    #         RETURNS TRIGGER AS $$
    #         DECLARE
    #             v_tenant_id UUID;
    #         BEGIN
    #             SELECT tenant_id INTO v_tenant_id 
    #             FROM local_users 
    #             WHERE id = COALESCE(NEW.user_id, OLD.user_id);
    #             
    #             INSERT INTO audit_logs (id, tenant_id, actor_user_id, action, entity_type, entity_id, created_at)
    #             VALUES (gen_random_uuid(), v_tenant_id, NEW.granted_by, TG_OP, 'user_role', COALESCE(OLD.id, NEW.id), NOW());
    #             RETURN NEW;
    #         END;
    #         $$ LANGUAGE plpgsql;
    #     ''')
    #     
    #     op.execute('''
    #         DROP TRIGGER IF EXISTS audit_user_roles_trigger ON user_roles;
    #         CREATE TRIGGER audit_user_roles_trigger
    #         AFTER INSERT OR UPDATE OR DELETE ON user_roles
    #         FOR EACH ROW EXECUTE FUNCTION audit_user_roles_trigger_func();
    #     ''')
    # except:
    #     pass


def downgrade() -> None:
    # Note: Trigger is already disabled in upgrade, no need to drop here
    op.execute("DELETE FROM e_its_roles WHERE role_name IN ('infoturbejuht', 'it_talitus', 'juhtkond')")
    op.execute("DELETE FROM app_tenants WHERE name = 'Default'")
    
    op.drop_column('memberships', 'local_user_id')
    op.drop_column('memberships', 'tenant_id')
    
    op.drop_table('user_roles')
    op.drop_table('e_its_roles')
    op.drop_table('local_users')
    op.drop_table('tenant_users')
    op.drop_table('global_users')
    op.drop_table('app_tenants')