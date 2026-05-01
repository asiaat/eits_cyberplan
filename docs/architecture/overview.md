# Architecture Overview

## System Context

The E-ITS Management System is a web-based compliance tool that helps organizations manage their information security implementation according to the Estonian Information Security Standard (E-ITS).

## Technology Stack

- **Frontend**: React 18 + TypeScript + Vite + Tailwind CSS + shadcn/ui
- **Backend**: Python 3.11 + FastAPI + SQLAlchemy 2.0 + Alembic
- **Database**: PostgreSQL 16
- **Cache/Queue**: Redis 7
- **Object Storage**: MinIO (S3-compatible)

## Architecture Layers

### Backend
```
app/
├── main.py           # FastAPI application entry
├── core/            # Config, security, audit
├── db/              # Session, base, init
├── models/          # SQLAlchemy models
├── schemas/         # Pydantic schemas
├── api/v1/          # API routes
```

### Frontend
```
src/
├── pages/            # Page components
├── components/      # Shared components
├── lib/             # API client, auth, utils
├── hooks/           # Custom hooks
```

## Security Model

1. **Authentication**: JWT-based with local user passwords (bcrypt hashed)
2. **Authorization**: Role-based access control (RBAC)
3. **Tenant Isolation**: All tenant-scoped data filtered by tenant_id
4. **Audit Logging**: All important changes logged to audit_logs table

## Data Flow

1. User logs in → JWT token issued
2. Frontend stores token → includes in Authorization header
3. Backend validates token → extracts user_id → checks permissions
4. All writes create audit log entries