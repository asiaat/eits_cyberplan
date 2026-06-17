# Business Processes

Core domain tables for business process management.

---

## `business_processes`

Represents a business process within an organization. Supports soft delete.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | UUID | PK | `uuid4` | Primary key |
| `tenant_id` | UUID | NOT NULL, FK → `app_tenants.id` | — | Tenant (INDEX) |
| `owner_user_id` | UUID | YES, FK → `local_users.id` | — | Process owner |
| `division_id` | UUID | YES | — | Organizational division (from `app_tenants.divisions`) |
| `name` | VARCHAR(255) | NOT NULL | — | Process name |
| `description` | TEXT | YES | — | Description |
| `purpose` | TEXT | YES | — | Purpose/objective of the process |
| `inputs` | TEXT | YES | — | Process inputs |
| `outputs` | TEXT | YES | — | Process outputs |
| `status` | VARCHAR(50) | YES | `'active'` | Status (`active`, `inactive`, `archived`) |
| `confidentiality_need` | VARCHAR(20) | YES | `'normal'` | Confidentiality protection need |
| `integrity_need` | VARCHAR(20) | YES | `'normal'` | Integrity protection need |
| `availability_need` | VARCHAR(20) | YES | `'normal'` | Availability protection need |
| `process_type` | VARCHAR(20) | YES | `'OPERATIVE'` | CHECK `IN ('OPERATIVE', 'SUPPORTING')` |
| `priority` | INTEGER | YES | `2` | CHECK `BETWEEN 1 AND 3` |
| `created_at` | TIMESTAMP | YES | `now()` | Creation timestamp |
| `updated_at` | TIMESTAMP | YES | `now()` | Last update timestamp |
| `deleted_at` | TIMESTAMP | YES | — | Soft delete timestamp (INDEX) |
| `deleted_by` | UUID | YES | — | Who deleted this record |

**Soft Delete:** Yes (via `SoftDeleteMixin`)

**Relationships:**
- `tenant` → `AppTenant`
- `owner_user` → `LocalUser`
- `assets` → `ProcessAsset` (assets linked to this process)
- `dependencies` → `BusinessProcessDependency`

**Protection Need Values:** `normal`, `high`, `very_high`, `unknown`

---

## `business_process_dependencies`

Tracks dependencies between business processes.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | UUID | PK | `uuid4` | Primary key |
| `tenant_id` | UUID | NOT NULL, FK → `app_tenants.id` | — | Tenant |
| `primary_process_id` | UUID | NOT NULL, FK → `business_processes.id` | — | The process that depends |
| `depends_on_process_id` | UUID | NOT NULL, FK → `business_processes.id` | — | The process being depended on |
| `dependency_type` | VARCHAR(50) | YES | — | Type of dependency |
| `description` | TEXT | YES | — | Description of the dependency |
| `created_at` | TIMESTAMP WITH TZ | YES | `now()` | Creation timestamp |

**Unique Constraints:** `(primary_process_id, depends_on_process_id)` → `uq_bp_dependency_pair`

**Relationships:**
- `tenant` → `AppTenant`
- `primary_process` → `BusinessProcess`
- `depends_on_process` → `BusinessProcess`

---

## `process_assets`

Junction table linking business processes to assets.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | UUID | PK | `uuid4` | Primary key |
| `tenant_id` | UUID | NOT NULL, FK → `app_tenants.id` | — | Tenant (INDEX) |
| `business_process_id` | UUID | NOT NULL, FK → `business_processes.id` | — | Business process |
| `asset_id` | UUID | NOT NULL, FK → `assets.id` | — | Asset |
| `relation_description` | TEXT | YES | — | How the asset relates to the process |

**Relationships:**
- `business_process` → `BusinessProcess`
- `asset` → `Asset`
