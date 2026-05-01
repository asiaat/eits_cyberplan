"""Database initialization and seeding."""
from sqlalchemy.orm import Session

from app.models.role import Role


DEFAULT_ROLES = [
    {"code": "admin", "name": "Administrator", "description": "Full system access"},
    {"code": "ism", "name": "Information Security Manager", "description": "Manage E-ITS implementation"},
    {"code": "process_owner", "name": "Process Owner", "description": "Owns business processes"},
    {"code": "asset_owner", "name": "Asset Owner", "description": "Owns assets"},
    {"code": "auditor", "name": "Auditor", "description": "Read-only access"},
]


def init_db(db: Session) -> None:
    """Initialize database with default data."""
    existing = db.query(Role).first()
    if existing is None:
        for role_data in DEFAULT_ROLES:
            role = Role(**role_data)
            db.add(role)
        db.commit()
    print("Database initialized with default roles.")