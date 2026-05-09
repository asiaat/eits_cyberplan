"""Database initialization and seeding."""
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.role import Role
from app.models.permission import Permission
from app.models.role_permission import RolePermission
from app.models.membership import Membership
from app.models.tenant import Tenant
from app.models.alert import Alert
from app.core.security import get_password_hash


DEFAULT_ROLES = [
    {"id": "admin", "code": "admin", "name": "Administrator", "description": "Full system access", "is_default": "true"},
    {"id": "ism", "code": "ism", "name": "Information Security Manager", "description": "Manage E-ITS implementation", "is_default": "true"},
    {"id": "process_owner", "code": "process_owner", "name": "Process Owner", "description": "Owns business processes", "is_default": "true"},
    {"id": "asset_owner", "code": "asset_owner", "name": "Asset Owner", "description": "Owns assets", "is_default": "true"},
    {"id": "auditor", "code": "auditor", "name": "Auditor", "description": "Read-only access", "is_default": "true"},
]

DEFAULT_PERMISSIONS = [
    # Users & Roles
    {"id": "users.view", "code": "users.view", "name": "View Users", "description": "View user list and details", "category": "users"},
    {"id": "users.create", "code": "users.create", "name": "Create Users", "description": "Create new users", "category": "users"},
    {"id": "users.edit", "code": "users.edit", "name": "Edit Users", "description": "Edit user details", "category": "users"},
    {"id": "users.delete", "code": "users.delete", "name": "Delete Users", "description": "Delete users", "category": "users"},
    {"id": "roles.manage", "code": "roles.manage", "name": "Manage Roles", "description": "Create, edit, delete roles", "category": "users"},
    {"id": "roles.assign", "code": "roles.assign", "name": "Assign Roles", "description": "Assign roles to users", "category": "users"},

    # Business Processes
    {"id": "processes.view", "code": "processes.view", "name": "View Processes", "description": "View business processes", "category": "processes"},
    {"id": "processes.create", "code": "processes.create", "name": "Create Processes", "description": "Create business processes", "category": "processes"},
    {"id": "processes.edit", "code": "processes.edit", "name": "Edit Processes", "description": "Edit business processes", "category": "processes"},
    {"id": "processes.delete", "code": "processes.delete", "name": "Delete Processes", "description": "Delete business processes", "category": "processes"},

    # Assets
    {"id": "assets.view", "code": "assets.view", "name": "View Assets", "description": "View assets", "category": "assets"},
    {"id": "assets.create", "code": "assets.create", "name": "Create Assets", "description": "Create assets", "category": "assets"},
    {"id": "assets.edit", "code": "assets.edit", "name": "Edit Assets", "description": "Edit assets", "category": "assets"},
    {"id": "assets.delete", "code": "assets.delete", "name": "Delete Assets", "description": "Delete assets", "category": "assets"},

    # Risks
    {"id": "risks.view", "code": "risks.view", "name": "View Risks", "description": "View risk register", "category": "risks"},
    {"id": "risks.create", "code": "risks.create", "name": "Create Risks", "description": "Create risks", "category": "risks"},
    {"id": "risks.edit", "code": "risks.edit", "name": "Edit Risks", "description": "Edit risks", "category": "risks"},
    {"id": "risks.delete", "code": "risks.delete", "name": "Delete Risks", "description": "Delete risks", "category": "risks"},

    # Evidence
    {"id": "evidence.view", "code": "evidence.view", "name": "View Evidence", "description": "View evidence", "category": "evidence"},
    {"id": "evidence.upload", "code": "evidence.upload", "name": "Upload Evidence", "description": "Upload evidence files", "category": "evidence"},
    {"id": "evidence.delete", "code": "evidence.delete", "name": "Delete Evidence", "description": "Delete evidence", "category": "evidence"},

    # Implementation Plan
    {"id": "implementation.view", "code": "implementation.view", "name": "View Implementation Plan", "description": "View implementation plan", "category": "implementation"},
    {"id": "implementation.manage", "code": "implementation.manage", "name": "Manage Implementation Plan", "description": "Manage implementation plan items", "category": "implementation"},

    # Dashboard & Reports
    {"id": "dashboard.view", "code": "dashboard.view", "name": "View Dashboard", "description": "View dashboard and statistics", "category": "dashboard"},
    {"id": "dashboard.export", "code": "dashboard.export", "name": "Export Data", "description": "Export reports and data", "category": "dashboard"},

    # Catalog & Mappings
    {"id": "catalog.view", "code": "catalog.view", "name": "View Catalog", "description": "View E-ITS catalog", "category": "catalog"},
    {"id": "mappings.view", "code": "mappings.view", "name": "View Mappings", "description": "View mappings", "category": "catalog"},
    {"id": "mappings.manage", "code": "mappings.manage", "name": "Manage Mappings", "description": "Manage object-module mappings", "category": "catalog"},

    # Audit
    {"id": "audit.view", "code": "audit.view", "name": "View Audit Logs", "description": "View audit logs", "category": "audit"},

    # Organization
    {"id": "organization.view", "code": "organization.view", "name": "View Organization", "description": "View organization details", "category": "organization"},
    {"id": "organization.edit", "code": "organization.edit", "name": "Edit Organization", "description": "Edit company and division details", "category": "organization"},
    {"id": "people.manage", "code": "people.manage", "name": "Manage People", "description": "Create, edit, delete people (person assets)", "category": "organization"},
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
        "organization.view", "organization.edit", "people.manage",
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
        "organization.view", "organization.edit", "people.manage",
    ],
    "process_owner": [
        "processes.view", "processes.edit",
        "evidence.view", "evidence.upload",
        "dashboard.view",
        "organization.view", "people.manage",
    ],
    "asset_owner": [
        "assets.view", "assets.edit",
        "evidence.view", "evidence.upload",
        "dashboard.view",
        "organization.view", "people.manage",
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
        "organization.view",
    ],
}

DEFAULT_USERS = [
    {"email": "admin@eits.ee", "name": "System Administrator", "password": "admin123", "role_code": "admin"},
]


def init_db(db: Session) -> None:
    """Initialize database with default data."""

    # Create roles
    existing_roles = db.query(Role).first()
    if existing_roles is None:
        for role_data in DEFAULT_ROLES:
            role = Role(**role_data)
            db.add(role)
        db.commit()
        print("Default roles created.")

    # Create permissions
    existing_perms = db.query(Permission).first()
    if existing_perms is None:
        for perm_data in DEFAULT_PERMISSIONS:
            perm = Permission(**perm_data)
            db.add(perm)
        db.commit()
        print("Default permissions created.")

    # Create role-permission mappings
    existing_mapping = db.query(RolePermission).first()
    if existing_mapping is None:
        for role_code, perm_codes in ROLE_PERMISSIONS.items():
            role = db.query(Role).filter(Role.code == role_code).first()
            if role:
                for perm_code in perm_codes:
                    perm = db.query(Permission).filter(Permission.code == perm_code).first()
                    if perm:
                        rp = RolePermission(role_id=role.id, permission_id=perm.id)
                        db.add(rp)
        db.commit()
        print("Default role-permission mappings created.")

    # Get or create default tenant
    default_tenant = db.query(Tenant).first()
    if default_tenant is None:
        default_tenant = Tenant(name="Default Organization", registry_code="DEFAULT")
        db.add(default_tenant)
        db.commit()
        db.refresh(default_tenant)
        print("Default tenant created.")

    # Create default users with roles
    existing_user = db.query(User).filter(User.email == "admin@eits.ee").first()
    if existing_user is None:
        for user_data in DEFAULT_USERS:
            user = User(
                email=user_data["email"],
                name=user_data["name"],
                hashed_password=get_password_hash(user_data["password"]),
            )
            db.add(user)
            db.flush()

            role = db.query(Role).filter(Role.code == user_data["role_code"]).first()
            if role:
                membership = Membership(user_id=user.id, role_id=role.id, tenant_id=default_tenant.id)
                db.add(membership)

        db.commit()
        print("Default users created with roles.")
    else:
        admin_role = db.query(Role).filter(Role.code == "admin").first()
        if admin_role:
            has_admin = db.query(Membership).filter(
                Membership.user_id == existing_user.id,
                Membership.role_id == admin_role.id
            ).first()
            if not has_admin:
                membership = Membership(user_id=existing_user.id, role_id=admin_role.id, tenant_id=default_tenant.id)
                db.add(membership)
                db.commit()
                print("Admin role assigned to existing admin user.")

    # Fix existing users without roles - assign auditor role
    auditor_role = db.query(Role).filter(Role.code == "auditor").first()
    if auditor_role:
        all_users = db.query(User).all()
        for user in all_users:
            has_membership = db.query(Membership).filter(Membership.user_id == user.id).first()
            if not has_membership:
                membership = Membership(user_id=user.id, role_id=auditor_role.id, tenant_id=default_tenant.id)
                db.add(membership)
                print(f"Assigned auditor role to existing user: {user.email}")
        db.commit()

    # Create default alerts
    existing_alerts = db.query(Alert).first()
    if existing_alerts is None:
        default_alerts = [
            {
                "title": "Welcome to CyberPlan",
                "message": "E-ITS Management System is ready. Configure your organization to get started.",
                "level": "info",
                "target_role": "all",
                "link": "/organization",
            },
            {
                "title": "Configure Your Organization",
                "message": "Add team members and assign roles to start managing your information security.",
                "level": "info",
                "target_role": "admin",
                "link": "/organization",
            },
            {
                "title": "Review Risk Register",
                "message": "You have risks that need assessment. Please review your risk register.",
                "level": "warning",
                "target_role": "ism",
                "link": "/risks",
            },
            {
                "title": "Evidence Required",
                "message": "Some controls need evidence documentation. Please upload supporting documents.",
                "level": "warning",
                "target_role": "admin",
                "link": "/evidences",
            },
            {
                "title": "Implementation Plan Update",
                "message": "Review your implementation plan to ensure timely completion of security measures.",
                "level": "info",
                "target_role": "all",
                "link": "/implementation-plan",
            },
        ]
        for alert_data in default_alerts:
            alert = Alert(**alert_data)
            db.add(alert)
        db.commit()
        print("Default alerts created.")

    # Daily cleanup: Mark old read alerts as inactive
    cleanup_old_alerts(db)

    print("Database initialized with E-ITS roles and permissions.")


def cleanup_old_alerts(db: Session):
    """Mark old read alerts as inactive (daily cleanup)."""
    from datetime import datetime, timedelta

    thresholds = {
        "error": 7,
        "warning": 14,
        "info": 30,
        "success": 7,
    }

    for level, days in thresholds.items():
        cutoff = datetime.utcnow() - timedelta(days=days)
        result = db.query(Alert).filter(
            Alert.level == level,
            Alert.is_read == "true",
            Alert.is_active == "true",
            Alert.read_at < cutoff
        ).update({"is_active": "false"})
        
    db.commit()