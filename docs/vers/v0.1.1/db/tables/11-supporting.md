# Supporting Tables

Secondary tables for audit logging, comments, people directory, alerts, protection needs, and reference data.

---

## `audit_logs`

Append-only event log tracking important changes to domain entities.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | UUID | PK | `uuid4` | Primary key |
| `tenant_id` | UUID | NOT NULL, FK → `app_tenants.id` | — | Tenant (INDEX) |
| `actor_user_id` | UUID | YES, FK → `global_users.id` | — | User who performed the action |
| `action` | VARCHAR(50) | NOT NULL | — | Action type (e.g., `create`, `update`, `delete`) |
| `entity_type` | VARCHAR(50) | NOT NULL | — | Type of affected entity (e.g., `business_process`, `risk`) |
| `entity_id` | UUID | NOT NULL | — | ID of the affected entity |
| `before_json` | TEXT | YES | — | JSON snapshot of state before change |
| `after_json` | TEXT | YES | — | JSON snapshot of state after change |
| `created_at` | TIMESTAMP | YES | `now()` | When the change occurred |

**Relationships:**
- `tenant` → `AppTenant`

---

## `comments`

Polymorphic comments on any entity type.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | UUID | PK | `uuid4` | Primary key |
| `tenant_id` | UUID | NOT NULL, FK → `app_tenants.id` | — | Tenant (INDEX) |
| `entity_type` | VARCHAR(50) | NOT NULL | — | Type of entity being commented on |
| `entity_id` | UUID | NOT NULL | — | ID of the entity |
| `author_user_id` | UUID | YES, FK → `users.id` | — | Comment author (legacy users) |
| `body` | TEXT | NOT NULL | — | Comment content |
| `created_at` | TIMESTAMP | YES | `now()` | Creation timestamp |

**Relationships:**
- `author_user` → `User` (legacy)

---

## `persons`

People directory. Represents individuals who may be assigned to assets. Supports soft delete.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | UUID | PK | `uuid4` | Primary key |
| `national_id` | VARCHAR(50) | YES | — | National ID number (UNIQUE) |
| `first_name` | VARCHAR(100) | NOT NULL | — | First name |
| `last_name` | VARCHAR(100) | NOT NULL | — | Last name |
| `date_of_birth` | DATE | YES | — | Date of birth |
| `email` | VARCHAR(255) | YES | — | Email address |
| `phone` | VARCHAR(50) | YES | — | Phone number |
| `additional_info` | TEXT | YES | — | Additional information |
| `created_at` | TIMESTAMP | YES | `now()` | Creation timestamp |
| `updated_at` | TIMESTAMP | YES | `now()` | Last update timestamp |
| `deleted_at` | TIMESTAMP | YES | — | Soft delete timestamp |
| `deleted_by` | UUID | YES | — | Who deleted this record |

**Soft Delete:** Yes

**Relationships:**
- `organizations` → `PersonOrganization`
- `assets` → `Asset`

---

## `person_organizations`

Junction table linking persons to organizations (tenants).

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | UUID | PK | `uuid4` | Primary key |
| `person_id` | UUID | NOT NULL, FK → `persons.id` | — | Person (RESTRICT on delete, INDEX) |
| `tenant_id` | UUID | NOT NULL, FK → `app_tenants.id` | — | Tenant (INDEX) |
| `role` | VARCHAR(100) | YES | — | Role within this organization |
| `created_at` | TIMESTAMP | YES | `now()` | Creation timestamp |

**Unique Constraints:** `(person_id, tenant_id)` → `uq_person_tenant`

**Relationships:**
- `person` → `Person`

---

## `organization_people`

Alternate person-to-organization linking table.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | UUID | PK | `uuid4` | Primary key |
| `tenant_id` | UUID | NOT NULL | — | Tenant (INDEX) |
| `person_asset_id` | UUID | NOT NULL | — | Person/asset ID (INDEX) |
| `created_at` | TIMESTAMP | YES | `now()` | Creation timestamp |

**Unique Constraints:** `(tenant_id, person_asset_id)` → `uq_org_person`

---

## `alerts`

System notifications/alerts for users.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | UUID | PK | `uuid4` | Primary key |
| `title` | VARCHAR(255) | NOT NULL | — | Alert title |
| `message` | TEXT | YES | — | Alert message body |
| `level` | ENUM | NOT NULL | `'info'` | ENUM `('info', 'warning', 'error', 'success')` |
| `target_role` | ENUM | NOT NULL | `'all'` | ENUM `('admin', 'ism', 'all')` |
| `is_read` | VARCHAR(10) | NOT NULL | `"false"` | Whether the alert has been read |
| `read_at` | TIMESTAMP | YES | — | When the alert was read |
| `created_at` | TIMESTAMP | YES | `now()` | Creation timestamp |
| `link` | VARCHAR(255) | YES | — | Deep link URL |
| `is_active` | VARCHAR(10) | NOT NULL | `"true"` | Whether alert is active |
| `tenant_id` | UUID | YES | — | Tenant (nullable for system-wide alerts) |

---

## `protection_need_summaries`

Consolidated protection needs for business processes, calculated from damage assessments.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | UUID | PK | `uuid4` | Primary key |
| `tenant_id` | UUID | NOT NULL, FK → `app_tenants.id` | — | Tenant (CASCADE DELETE) |
| `business_process_id` | UUID | NOT NULL, FK → `business_processes.id` | — | BP (CASCADE DELETE) |
| `protection_need` | VARCHAR(20) | NOT NULL | `'NORMAL'` | CHECK `IN ('NORMAL', 'HIGH', 'VERY_HIGH')` |
| `confidentiality_need` | VARCHAR(20) | YES | `'NORMAL'` | CHECK `IN ('NORMAL', 'HIGH', 'VERY_HIGH')` |
| `integrity_need` | VARCHAR(20) | YES | `'NORMAL'` | CHECK `IN ('NORMAL', 'HIGH', 'VERY_HIGH')` |
| `availability_need` | VARCHAR(20) | YES | `'NORMAL'` | CHECK `IN ('NORMAL', 'HIGH', 'VERY_HIGH')` |
| `justification` | TEXT | YES | — | Rationale |
| `approved_by` | UUID | YES, FK → `local_users.id` | — | Approver (SET NULL on delete) |
| `approved_at` | TIMESTAMP WITH TZ | YES | — | Approval timestamp |
| `created_at` | TIMESTAMP WITH TZ | YES | `now()` | Creation timestamp |
| `updated_at` | TIMESTAMP WITH TZ | YES | `now()` | Last update timestamp |

**Unique Constraints:** `(tenant_id, business_process_id)` → `uq_protection_need_summary`

**Static Calculation:** `level_from_damage(damage_category)`: <=1 → NORMAL, 2 → HIGH, >=3 → VERY_HIGH

**Relationships:**
- `tenant` → `AppTenant`
- `business_process` → `BusinessProcess`
- `approved_by_user` → `LocalUser`

---

## `asset_type_categories`

Reference data for asset category codes (T/V/I/R/A).

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | UUID | PK | `uuid4` | Primary key |
| `code` | VARCHAR(5) | NOT NULL | — | Category code (UNIQUE) |
| `name` | VARCHAR(100) | NOT NULL | — | Category name |
| `description` | TEXT | YES | — | Description |

**Seed Data:**

| Code | Name | Description |
|------|------|-------------|
| `T` | Infrastructure | Basic infrastructure |
| `V` | Network components | Network components |
| `I` | IT systems | IT systems |
| `R` | Applications | Applications |
| `A` | Industrial automation | Industrial automation systems |
