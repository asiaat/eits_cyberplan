# Legacy Tables (In Migration)

These tables are from the original v1 implementation. They are being gradually replaced by the Tier A and Tier B equivalents. New code should use Tier A/B tables where possible.

---

## `tenants`

Legacy tenant table (being superseded by `app_tenants`).

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | UUID | PK | `uuid4` | Primary key |
| `name` | VARCHAR(255) | NOT NULL | — | Organization name |
| `registry_code` | VARCHAR(20) | YES | — | Registry code (UNIQUE) |
| `legal_form` | VARCHAR(50) | YES | — | Legal form |
| `registration_date` | DATE | YES | — | Registration date |
| `status` | VARCHAR(50) | YES | — | Status |
| `registered_address` | TEXT | YES | — | Registered address |
| `contact_address` | TEXT | YES | — | Contact address |
| `phone` | VARCHAR(50) | YES | — | Phone |
| `email` | VARCHAR(255) | YES | — | Email |
| `website` | VARCHAR(255) | YES | — | Website |
| `share_capital` | NUMERIC(15,2) | YES | — | Share capital |
| `nace_codes` | JSON | YES | — | NACE classification codes |
| `company_type` | VARCHAR(20) | YES | — | Company type |
| `parent_company_id` | UUID | YES, FK → `tenants.id` | — | Parent company (self-ref) |
| `divisions` | JSON | YES | `[]` | Organizational divisions |
| `created_at` | TIMESTAMP | YES | `now()` | Creation timestamp |
| `updated_at` | TIMESTAMP | YES | `now()` | Last update timestamp |

**Relationships:**
- `child_tenants` → self-referential via `parent_company_id`

---

## `users`

Legacy user table (being superseded by `global_users` + `local_users`).

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | UUID | PK | `uuid4` | Primary key |
| `email` | VARCHAR(255) | NOT NULL | — | Email (UNIQUE, INDEX) |
| `name` | VARCHAR(255) | NOT NULL | — | Display name |
| `auth_provider` | VARCHAR(50) | YES | `'local'` | Authentication provider |
| `hashed_password` | VARCHAR(255) | YES | — | Password hash |
| `is_active` | BOOLEAN | YES | `True` | Active status |
| `created_at` | TIMESTAMP | YES | `now()` | Creation timestamp |

**Relationships:**
- `memberships` → `Membership`
- `owned_assets` → `Asset` (via `owner_user_id`)
- `owned_implementation_items` → `ImplementationPlanItem`
- `owned_risks` → `Risk`
- `mappings` → `ObjectModuleMapping`
- `comments` → `Comment`

---

## `roles`

Legacy role definitions (being superseded by `e_its_roles`).

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | TEXT | PK | — | Primary key (text) |
| `code` | VARCHAR(50) | NOT NULL | — | Role code (UNIQUE) |
| `name` | VARCHAR(100) | NOT NULL | — | Display name |
| `description` | TEXT | YES | — | Description |
| `is_default` | VARCHAR(10) | YES | `'false'` | Whether this is a default role |

**Relationships:**
- `memberships` → `Membership`
- `role_permissions` → `RolePermission`

---

## `permissions`

Permission definitions (shared with Tier B system). See `02-tier-b-iam.md` for full column details.

33 permissions across 9 categories. Referenced by both `role_permissions` (legacy) and `e_its_role_permissions` (Tier B).

---

## `role_permissions`

Legacy junction table linking roles to permissions.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `role_id` | TEXT | PK, FK → `roles.id` | — | Role (CASCADE DELETE) |
| `permission_id` | TEXT | PK, FK → `permissions.id` | — | Permission (CASCADE DELETE) |

**Primary Key:** Composite `(role_id, permission_id)`

---

## `memberships`

Legacy junction table linking users to tenants with a role.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | UUID | PK | `uuid4` | Primary key |
| `tenant_id` | UUID | YES, FK → `app_tenants.id` | — | Tenant |
| `user_id` | UUID | NOT NULL, FK → `users.id` | — | User |
| `role_id` | VARCHAR(50) | NOT NULL, FK → `roles.id` | — | Role |
| `local_user_id` | UUID | YES, FK → `local_users.id` | — | Local user (Tier B link) |

**Relationships:**
- `user` → `User` (legacy)
- `role` → `Role` (legacy)
- `local_user` → `LocalUser` (Tier B)
