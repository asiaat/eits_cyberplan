# Tier B — Per-Tenant IAM

Each tenant has its own user profiles, roles, and permissions. All tables are tenant-scoped.

---

## `local_users`

Per-tenant user profiles linked to a global identity.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | UUID | PK | `uuid4` | Primary key |
| `global_user_id` | UUID | NOT NULL, FK → `global_users.id` | — | Global identity (CASCADE DELETE) |
| `tenant_id` | UUID | NOT NULL, FK → `app_tenants.id` | — | Tenant (CASCADE DELETE) |
| `full_name` | VARCHAR(255) | NOT NULL | — | Display name |
| `department` | VARCHAR(100) | YES | — | Department within organization |
| `is_active` | BOOLEAN | YES | `True` | Whether user is active in this tenant |
| `created_at` | TIMESTAMP | YES | `now()` | Creation timestamp |

**Unique Constraints:** `(global_user_id, tenant_id)` → `uq_local_user_global_tenant`

**Relationships:**
- `global_user` → `GlobalUser`
- `tenant` → `AppTenant`
- `memberships` → `Membership` (legacy)
- `owned_business_processes` → `BusinessProcess`
- `owned_evidences` → `Evidence`
- `user_roles` → `UserRole` (role assignments)

---

## `e_its_roles`

Per-tenant role definitions. Standard roles: `admin`, `ism`, `process_owner`, `asset_owner`, `auditor`.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | UUID | PK | `uuid4` | Primary key |
| `tenant_id` | UUID | NOT NULL, FK → `app_tenants.id` | — | Tenant (CASCADE DELETE) |
| `role_name` | VARCHAR(100) | NOT NULL | — | Role name/code |
| `description` | TEXT | YES | — | Role description |

**Unique Constraints:** `(tenant_id, role_name)` → `uq_e_its_role_tenant`

**Relationships:**
- `tenant` → `AppTenant`
- `user_roles` → `UserRole`
- `role_permissions` → `EITSRolePermission`

---

## `user_roles`

Junction table: which roles are assigned to which users. Maintains audit trail of who granted the role.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | UUID | PK | `uuid4` | Primary key |
| `user_id` | UUID | NOT NULL, FK → `local_users.id` | — | Local user (CASCADE DELETE) |
| `role_id` | UUID | NOT NULL, FK → `e_its_roles.id` | — | Role (CASCADE DELETE) |
| `granted_by` | UUID | YES, FK → `local_users.id` | — | Who granted this role |
| `granted_at` | TIMESTAMP | YES | `now()` | When the role was granted |

**Relationships:**
- `local_user` → `LocalUser` (via `user_id`)
- `granted_by_user` → `LocalUser` (via `granted_by`)
- `e_its_role` → `EITSRole`

---

## `e_its_role_permissions`

Junction table: which permissions each role has.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `role_id` | UUID | PK, FK → `e_its_roles.id` | — | Role (CASCADE DELETE) |
| `permission_id` | TEXT | PK, FK → `permissions.id` | — | Permission code (CASCADE DELETE) |

**Primary Key:** Composite `(role_id, permission_id)`

**Relationships:**
- `role` → `EITSRole`
- `permission` → `Permission`

---

## `permissions`

Shared permission definitions (used by both legacy and Tier B systems).

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | TEXT | PK | — | Primary key (text code) |
| `code` | VARCHAR(100) | NOT NULL | — | Permission code (UNIQUE) |
| `name` | VARCHAR(100) | NOT NULL | — | Display name |
| `description` | TEXT | YES | — | Description |
| `category` | VARCHAR(50) | YES | — | Permission category (e.g., `users`, `processes`, `assets`) |

**Seed Data:** 33 permissions across 9 categories (see `seed-data.md`).

**Relationships:**
- `role_permissions` → `RolePermission` (legacy)
- `e_its_role_permissions` → `EITSRolePermission`
