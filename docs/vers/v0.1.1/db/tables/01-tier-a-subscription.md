# Tier A — Subscription Layer

These tables manage tenant subscriptions and global user identities. They are the **only tables without `tenant_id`** — they operate at the system level.

---

## `app_tenants`

Tenant/organization registry. Each row represents a customer organization using the system.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | UUID | PK | `uuid4` | Primary key |
| `name` | VARCHAR(255) | NOT NULL | — | Organization name |
| `status` | VARCHAR(50) | YES | `'active'` | Tenant status |
| `plan` | VARCHAR(50) | YES | — | Subscription plan |
| `registry_code` | VARCHAR(50) | YES | — | Organization registry code |
| `legal_form` | VARCHAR(255) | YES | — | Legal form of organization |
| `registered_address` | VARCHAR(500) | YES | — | Official registered address |
| `phone` | VARCHAR(50) | YES | — | Contact phone |
| `email` | VARCHAR(255) | YES | — | Contact email |
| `divisions` | VARCHAR(5000) | YES | — | JSON array of `{id, name}` divisions |
| `created_at` | TIMESTAMP | YES | `now()` | Creation timestamp |

**Relationships:**
- `tenant_users` → `TenantUser` (tenant membership)
- `local_users` → `LocalUser` (per-tenant user profiles)
- `e_its_roles` → `EITSRole` (per-tenant roles)
- `audit_logs` → `AuditLog`
- `business_processes` → `BusinessProcess`
- `security_profiles` → `SecurityProfile`
- `protectionmode_selections` → `ProtectionModeSelection`

---

## `global_users`

Global user identities. One user can access multiple tenants.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | UUID | PK | `uuid4` | Primary key |
| `email` | VARCHAR(255) | NOT NULL | — | Email address (UNIQUE, INDEX) |
| `password_hash` | VARCHAR(255) | NOT NULL | — | Bcrypt password hash |
| `mfa_enabled` | BOOLEAN | YES | `False` | MFA enabled flag |
| `mfa_secret` | VARCHAR(255) | YES | — | MFA TOTP secret |
| `created_at` | TIMESTAMP | YES | `now()` | Creation timestamp |

**Unique Constraints:** `email` (UNIQUE, INDEXED)

**Relationships:**
- `tenant_users` → `TenantUser` (junction to tenants)
- `local_users` → `LocalUser` (per-tenant profiles)

---

## `tenant_users`

Junction table mapping global users to tenants (which tenants a user can access).

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `tenant_id` | UUID | PK, FK → `app_tenants.id` | — | Tenant (CASCADE DELETE) |
| `user_id` | UUID | PK, FK → `global_users.id` | — | Global user (CASCADE DELETE) |
| `assigned_at` | TIMESTAMP | YES | `now()` | When the user was assigned to this tenant |

**Primary Key:** Composite `(tenant_id, user_id)`

**Relationships:**
- `tenant` → `AppTenant`
- `user` → `GlobalUser`
