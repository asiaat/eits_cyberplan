"""Database initialization and seeding."""
from sqlalchemy.orm import Session

from app.models.app_tenant import GlobalUser, TenantUser, AppTenant
from app.models.local_user import LocalUser, EITSRole, UserRole
from app.models.e_its_role_permission import EITSRolePermission
from app.models.permission import Permission
from app.core.security import get_password_hash


DEFAULT_ROLES = [
    {"role_name": "admin", "description": "Full system access"},
    {"role_name": "ism", "description": "Manage E-ITS implementation"},
    {"role_name": "process_owner", "description": "Owns business processes"},
    {"role_name": "asset_owner", "description": "Owns assets"},
    {"role_name": "auditor", "description": "Read-only access"},
]

DEFAULT_PERMISSIONS = [
    {"code": "users.view", "name": "View Users", "description": "View user list and details", "category": "users"},
    {"code": "users.create", "name": "Create Users", "description": "Create new users", "category": "users"},
    {"code": "users.edit", "name": "Edit Users", "description": "Edit user details", "category": "users"},
    {"code": "users.delete", "name": "Delete Users", "description": "Delete users", "category": "users"},
    {"code": "roles.manage", "name": "Manage Roles", "description": "Create, edit, delete roles", "category": "users"},
    {"code": "roles.assign", "name": "Assign Roles", "description": "Assign roles to users", "category": "users"},
    {"code": "processes.view", "name": "View Processes", "description": "View business processes", "category": "processes"},
    {"code": "processes.create", "name": "Create Processes", "description": "Create business processes", "category": "processes"},
    {"code": "processes.edit", "name": "Edit Processes", "description": "Edit business processes", "category": "processes"},
    {"code": "processes.delete", "name": "Delete Processes", "description": "Delete business processes", "category": "processes"},
    {"code": "assets.view", "name": "View Assets", "description": "View assets", "category": "assets"},
    {"code": "assets.create", "name": "Create Assets", "description": "Create assets", "category": "assets"},
    {"code": "assets.edit", "name": "Edit Assets", "description": "Edit assets", "category": "assets"},
    {"code": "assets.delete", "name": "Delete Assets", "description": "Delete assets", "category": "assets"},
    {"code": "risks.view", "name": "View Risks", "description": "View risk register", "category": "risks"},
    {"code": "risks.create", "name": "Create Risks", "description": "Create risks", "category": "risks"},
    {"code": "risks.edit", "name": "Edit Risks", "description": "Edit risks", "category": "risks"},
    {"code": "risks.delete", "name": "Delete Risks", "description": "Delete risks", "category": "risks"},
    {"code": "evidence.view", "name": "View Evidence", "description": "View evidence", "category": "evidence"},
    {"code": "evidence.upload", "name": "Upload Evidence", "description": "Upload evidence files", "category": "evidence"},
    {"code": "evidence.delete", "name": "Delete Evidence", "description": "Delete evidence", "category": "evidence"},
    {"code": "implementation.view", "name": "View Implementation Plan", "description": "View implementation plan", "category": "implementation"},
    {"code": "implementation.manage", "name": "Manage Implementation Plan", "description": "Manage implementation plan items", "category": "implementation"},
    {"code": "dashboard.view", "name": "View Dashboard", "description": "View dashboard and statistics", "category": "dashboard"},
    {"code": "dashboard.export", "name": "Export Data", "description": "Export reports and data", "category": "dashboard"},
    {"code": "catalog.view", "name": "View Catalog", "description": "View E-ITS catalog", "category": "catalog"},
    {"code": "mappings.view", "name": "View Mappings", "description": "View mappings", "category": "catalog"},
    {"code": "mappings.manage", "name": "Manage Mappings", "description": "Manage object-module mappings", "category": "catalog"},
    {"code": "audit.view", "name": "View Audit Logs", "description": "View audit logs", "category": "audit"},
    {"code": "organizations.view", "name": "View Organizations", "description": "View all organizations", "category": "organizations"},
    {"code": "organizations.create", "name": "Create Organizations", "description": "Create new organizations", "category": "organizations"},
    {"code": "people.view", "name": "View People", "description": "View people directory", "category": "people"},
    {"code": "people.create", "name": "Create People", "description": "Create new people in directory", "category": "people"},
    {"code": "people.edit", "name": "Edit People", "description": "Edit people in directory", "category": "people"},
    {"code": "people.delete", "name": "Delete People", "description": "Delete people from directory", "category": "people"},
]

ROLE_PERMISSIONS = {
    "admin": [
        "users.view", "users.create", "users.edit", "users.delete",
        "roles.manage", "roles.assign",
        "processes.view", "processes.create", "processes.edit", "processes.delete",
        "assets.view", "assets.create", "assets.edit", "assets.delete",
        "risks.view", "risks.create", "risks.edit", "risks.delete",
        "evidence.view", "evidence.upload", "evidence.delete",
        "implementation.view", "implementation.manage",
        "dashboard.view", "dashboard.export",
        "catalog.view", "mappings.view", "mappings.manage",
        "audit.view",
        "organizations.view", "organizations.create",
        "people.view", "people.create", "people.edit", "people.delete",
    ],
    "ism": [
        "processes.view", "processes.create", "processes.edit", "processes.delete",
        "assets.view", "assets.create", "assets.edit", "assets.delete",
        "risks.view", "risks.create", "risks.edit", "risks.delete",
        "evidence.view", "evidence.upload", "evidence.delete",
        "implementation.view", "implementation.manage",
        "dashboard.view", "dashboard.export",
        "catalog.view", "mappings.view", "mappings.manage",
        "audit.view",
        "organizations.view", "organizations.create",
        "people.view", "people.create", "people.edit", "people.delete",
    ],
    "process_owner": [
        "processes.view", "processes.edit",
        "evidence.view", "evidence.upload",
        "dashboard.view",
    ],
    "asset_owner": [
        "assets.view", "assets.edit",
        "evidence.view", "evidence.upload",
        "dashboard.view",
    ],
    "auditor": [
        "users.view",
        "processes.view",
        "assets.view",
        "risks.view",
        "evidence.view",
        "implementation.view",
        "dashboard.view", "dashboard.export",
        "catalog.view", "mappings.view",
        "audit.view",
    ],
}

DEFAULT_ADMIN_EMAIL = "admin@eits.ee"
DEFAULT_ADMIN_PASSWORD = "admin123"
DEFAULT_ADMIN_NAME = "System Administrator"


def init_db(db: Session) -> None:
    """Initialize database with default data."""

    # 1. Get or create default tenant FIRST
    default_tenant = db.query(AppTenant).filter(AppTenant.name == "Default").first()
    if default_tenant is None:
        default_tenant = AppTenant(name="Default", status="active", plan="enterprise")
        db.add(default_tenant)
        db.commit()
        db.refresh(default_tenant)
        print("Default tenant created.")

    # 2. Create permissions
    existing_perms = db.query(Permission).first()
    if existing_perms is None:
        for perm_data in DEFAULT_PERMISSIONS:
            perm = Permission(**perm_data)
            db.add(perm)
        db.commit()
        print("Default permissions created.")

    # 3. Create E-ITS roles for the default tenant
    existing_roles = db.query(EITSRole).filter(EITSRole.tenant_id == default_tenant.id).first()
    if existing_roles is None:
        for role_data in DEFAULT_ROLES:
            role = EITSRole(tenant_id=default_tenant.id, **role_data)
            db.add(role)
        db.commit()
        print("Default E-ITS roles created.")

        # Create role-permission mappings
        for role_code, perm_codes in ROLE_PERMISSIONS.items():
            role = db.query(EITSRole).filter(
                EITSRole.role_name == role_code,
                EITSRole.tenant_id == default_tenant.id
            ).first()
            if role:
                for perm_code in perm_codes:
                    perm = db.query(Permission).filter(Permission.code == perm_code).first()
                    if perm:
                        rp = EITSRolePermission(role_id=role.id, permission_id=perm.id)
                        db.add(rp)
        db.commit()
        print("Default role-permission mappings created.")

    # 4. Create admin global user
    existing_global_user = db.query(GlobalUser).filter(GlobalUser.email == DEFAULT_ADMIN_EMAIL).first()
    if existing_global_user is None:
        global_user = GlobalUser(
            email=DEFAULT_ADMIN_EMAIL,
            password_hash=get_password_hash(DEFAULT_ADMIN_PASSWORD)
        )
        db.add(global_user)
        db.commit()
        db.refresh(global_user)
        print("Admin global user created.")

        # Create tenant-user mapping
        tenant_user = TenantUser(tenant_id=default_tenant.id, user_id=global_user.id)
        db.add(tenant_user)

        # Create local user
        local_user = LocalUser(
            global_user_id=global_user.id,
            tenant_id=default_tenant.id,
            full_name=DEFAULT_ADMIN_NAME
        )
        db.add(local_user)
        db.commit()
        db.refresh(local_user)
        print("Admin local user created with tenant membership.")

        # Assign admin role to the local user
        admin_role = db.query(EITSRole).filter(
            EITSRole.role_name == "admin",
            EITSRole.tenant_id == default_tenant.id
        ).first()
        if admin_role:
            user_role = UserRole(user_id=local_user.id, role_id=admin_role.id)
            db.add(user_role)
            db.commit()
            print("Admin role assigned to admin user.")
    else:
        print("Admin global user already exists.")

    print("Database initialized with E-ITS roles and permissions.")