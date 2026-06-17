# Module Mappings and Security Profiles

Tables for mapping E-ITS modules to assets, business processes, and other target objects, plus protection mode/security profile configuration.

---

## `object_module_mappings`

Polymorphic mapping of E-ITS modules to any target object (asset, business process, etc.).

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | UUID | PK | `uuid4` | Primary key |
| `tenant_id` | UUID | NOT NULL, FK → `app_tenants.id` | — | Tenant (INDEX) |
| `target_type` | VARCHAR(50) | NOT NULL | — | Type of target object (e.g., `asset`, `business_process`) |
| `target_id` | UUID | NOT NULL | — | ID of the target object |
| `module_id` | UUID | NOT NULL, FK → `eits_modules.id` | — | The mapped module |
| `applicability` | VARCHAR(50) | YES | `'pending'` | Applicability status (`applicable`, `not_applicable`, `pending`) |
| `rationale` | TEXT | YES | — | Reason for this mapping decision |
| `selected_by_user_id` | UUID | YES, FK → `users.id` | — | User who created the mapping |
| `selected_at` | TIMESTAMP | YES | `now()` | When the mapping was created |

**Relationships:**
- `module` → `EitsModule`
- `selected_by_user` → `User` (legacy)

---

## `asset_module_mappings`

Maps assets to E-ITS modules (modeling). Generates IMR items.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | UUID | PK | `uuid4` | Primary key |
| `tenant_id` | UUID | NOT NULL, FK → `app_tenants.id` | — | Tenant (CASCADE DELETE, INDEX) |
| `asset_id` | UUID | NOT NULL, FK → `assets.id` | — | Asset (CASCADE DELETE, INDEX) |
| `module_id` | UUID | NOT NULL, FK → `eits_modules.id` | — | Module (CASCADE DELETE) |
| `justification` | TEXT | YES | — | Why this module was selected |
| `modeled_by` | UUID | YES, FK → `local_users.id` | — | Who performed the modeling (SET NULL on delete) |
| `modeled_at` | TIMESTAMP WITH TZ | YES | `now()` | When modeled |

**Unique Constraints:** `(tenant_id, asset_id, module_id)` → `uq_asset_module_mapping`

**Relationships:**
- `tenant` → `AppTenant`
- `asset` → `Asset`
- `module` → `EitsModule`
- `modeled_by_user` → `LocalUser`
- `imr_items` → `ImrItem`

---

## `bp_module_mappings`

Maps business processes to E-ITS modules (modeling). Generates IMR items for process-level measures.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | UUID | PK | `uuid4` | Primary key |
| `tenant_id` | UUID | NOT NULL, FK → `app_tenants.id` | — | Tenant (CASCADE DELETE) |
| `business_process_id` | UUID | NOT NULL, FK → `business_processes.id` | — | Business process (CASCADE DELETE, INDEX) |
| `module_id` | UUID | NOT NULL, FK → `eits_modules.id` | — | Module (CASCADE DELETE) |
| `justification` | TEXT | YES | — | Why this module was selected |
| `modeled_by` | UUID | YES, FK → `local_users.id` | — | Who performed the modeling (SET NULL on delete) |
| `modeled_at` | TIMESTAMP WITH TZ | YES | `now()` | When modeled |

**Unique Constraints:** `(tenant_id, business_process_id, module_id)` → `uq_bp_module_mapping`

**Relationships:**
- `tenant` → `AppTenant`
- `business_process` → `BusinessProcess`
- `module` → `EitsModule`
- `modeled_by_user` → `LocalUser`
- `imr_items` → `ImrItem`

---

## `process_module_assignments`

Per-tenant assignment of module applicability (which process modules apply to this organization).

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | UUID | PK | `uuid4` | Primary key |
| `tenant_id` | UUID | NOT NULL, FK → `app_tenants.id` | — | Tenant (CASCADE DELETE) |
| `module_id` | UUID | NOT NULL, FK → `eits_modules.id` | — | Module (CASCADE DELETE) |
| `is_applicable` | VARCHAR(1) | YES | `'1'` | Whether the module is applicable |
| `non_applicability_justification` | TEXT | YES | — | Reason if not applicable |
| `assigned_by` | UUID | YES, FK → `local_users.id` | — | Who assigned (SET NULL on delete) |
| `assigned_at` | TIMESTAMP WITH TZ | YES | `now()` | When assigned |

**Unique Constraints:** `(tenant_id, module_id)` → `uq_process_module_assignment`

**Relationships:**
- `tenant` → `AppTenant`
- `module` → `EitsModule`
- `assigned_by_user` → `LocalUser`

---

## `protectionmode_selections`

Tenant's selection of protection mode/security approach. Supports soft delete.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | UUID | PK | `uuid4` | Primary key |
| `tenant_id` | UUID | NOT NULL, FK → `app_tenants.id` | — | Tenant (CASCADE DELETE) |
| `catalog_version_id` | UUID | YES, FK → `eits_catalog_versions.id` | — | Catalog version (SET NULL on delete) |
| `security_approach` | VARCHAR(20) | NOT NULL | `'BASIC'` | Approach (`BASIC`, `STANDARD`, `CORE`) |
| `evidence_id` | UUID | YES, FK → `evidences.id` | — | Supporting evidence (SET NULL on delete) |
| `approved_by` | UUID | YES, FK → `local_users.id` | — | Who approved (SET NULL on delete) |
| `approved_at` | TIMESTAMP WITH TZ | YES | — | When approved |
| `notes` | TEXT | YES | — | Additional notes |
| `is_active` | BOOLEAN | NOT NULL | `True` | Whether this selection is active |
| `created_at` | TIMESTAMP WITH TZ | YES | `now()` | Creation timestamp |
| `updated_at` | TIMESTAMP WITH TZ | YES | `now()` | Last update timestamp |
| `deleted_at` | TIMESTAMP WITH TZ | YES | — | Soft delete timestamp |
| `deleted_by` | UUID | YES | — | Who deleted this record |

**Relationships:**
- `tenant` → `AppTenant`
- `catalog_version` → `EitsCatalogVersion`
- `evidence` → `Evidence`
- `approved_by_user` → `LocalUser`

---

## `security_profiles`

Per-tenant security approach/profile configuration. Supports soft delete.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | UUID | PK | `uuid4` | Primary key |
| `tenant_id` | UUID | NOT NULL, FK → `app_tenants.id` | — | Tenant (CASCADE DELETE, INDEX) |
| `catalog_version_id` | UUID | YES, FK → `eits_catalog_versions.id` | — | Catalog version (SET NULL on delete) |
| `security_approach` | VARCHAR(20) | NOT NULL | `'BASIC'` | CHECK `IN ('BASIC', 'STANDARD', 'CORE')` |
| `approved_by` | UUID | YES, FK → `local_users.id` | — | Who approved (SET NULL on delete) |
| `approved_at` | TIMESTAMP WITH TZ | YES | — | When approved |
| `notes` | TEXT | YES | — | Additional notes |
| `created_at` | TIMESTAMP WITH TZ | YES | `now()` | Creation timestamp |
| `updated_at` | TIMESTAMP WITH TZ | YES | `now()` | Last update timestamp |
| `deleted_at` | TIMESTAMP WITH TZ | YES | — | Soft delete timestamp |
| `deleted_by` | UUID | YES | — | Who deleted this record |

**Unique Constraints:** `(tenant_id, catalog_version_id)` → `uq_security_profile_tenant_version`

**Relationships:**
- `tenant` → `AppTenant`
- `catalog_version` → `EitsCatalogVersion`
- `approved_by_user` → `LocalUser`
