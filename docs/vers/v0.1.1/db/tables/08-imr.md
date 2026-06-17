# IMR — Implementation Plan

The core implementation plan tables. IMR = Information security Measures Implementation Plan.

---

## `imr_items`

Individual implementation items in the IMR. Supports soft delete. Each item represents one measure applied to one target object.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | UUID | PK | `uuid4` | Primary key |
| `tenant_id` | UUID | NOT NULL, FK → `app_tenants.id` | — | Tenant (CASCADE DELETE, INDEX) |
| `asset_module_mapping_id` | UUID | YES, FK → `asset_module_mappings.id` | — | Source asset-module mapping (CASCADE DELETE) |
| `bp_module_mapping_id` | UUID | YES, FK → `bp_module_mappings.id` | — | Source BP-module mapping (CASCADE DELETE, INDEX) |
| `measure_id` | UUID | NOT NULL, FK → `eits_catalog_measures.id` | — | The E-ITS catalog measure (CASCADE DELETE) |
| `is_process_module_measure` | BOOLEAN | YES | `False` | Whether this came from a process module |
| `pearo_status` | VARCHAR(1) | NOT NULL | `'E'` | PEARO status: `P`=Not Applicable, `E`=Not Implemented, `A`=Accepted Risk, `R`=Implemented, `O`=Partially Implemented |
| `implementation_description` | TEXT | YES | — | Description of implementation |
| `non_implementation_justification` | TEXT | YES | — | Reason if not implemented |
| `partial_scope_description` | TEXT | YES | — | Scope of partial implementation |
| `responsible_user_id` | UUID | YES, FK → `local_users.id` | — | Responsible person (SET NULL on delete) |
| `due_date` | DATE | YES | — | Target completion date |
| `next_review_date` | DATE | YES | — | Next review date |
| `priority` | VARCHAR(5) | YES | `'P2'` | Priority: `P1` (High), `P2` (Medium), `P3` (Low) |
| `risk_acceptance_approved_by` | UUID | YES, FK → `local_users.id` | — | Who approved risk acceptance (SET NULL on delete) |
| `risk_acceptance_date` | TIMESTAMP WITH TZ | YES | — | When risk acceptance was approved |
| `verification_method` | TEXT | YES | — | How implementation is verified |
| `last_verified_at` | TIMESTAMP WITH TZ | YES | — | When last verified |
| `imr_snapshot_id` | UUID | YES, FK → `imr_snapshots.id` | — | Snapshot this item belongs to (SET NULL on delete, INDEX) |
| `created_by` | UUID | YES, FK → `local_users.id` | — | Who created this item (SET NULL on delete, INDEX) |
| `updated_by` | UUID | YES, FK → `local_users.id` | — | Who last updated this item (SET NULL on delete) |
| `status_changed_at` | TIMESTAMP WITH TZ | YES | — | When status last changed |
| `requirement_profile` | VARCHAR(20) | YES | — | Requirement profile identifier |
| `todo_description` | TEXT | YES | — | Action/todo description |
| `cost_eur` | NUMERIC(12,2) | YES | — | Estimated cost in EUR |
| `created_at` | TIMESTAMP WITH TZ | YES | `now()` | Creation timestamp |
| `updated_at` | TIMESTAMP WITH TZ | YES | `now()` | Last update timestamp |
| `deleted_at` | TIMESTAMP WITH TZ | YES | — | Soft delete timestamp |
| `deleted_by` | UUID | YES | — | Who deleted this record |

**Soft Delete:** Yes

**PEARO Status Legend:**

| Code | Meaning | Description |
|------|---------|-------------|
| `P` | Not Applicable | Measure is not applicable to this target |
| `E` | Not Implemented | Measure has not been implemented |
| `A` | Accepted Risk | Risk has been accepted instead of implementing |
| `R` | Implemented | Measure is fully implemented |
| `O` | Partially Implemented | Measure is partially implemented |

**Relationships:**
- `tenant` → `AppTenant`
- `imr_snapshot` → `ImrSnapshot`
- `asset_module_mapping` → `AssetModuleMapping`
- `bp_module_mapping` → `BusinessProcessModuleMapping`
- `measure` → `EitsCatalogMeasure`
- `responsible_user` → `LocalUser`
- `risk_acceptance_approver` → `LocalUser`
- `risk_measure_links` → `RiskMeasureLink`
- `creator` → `LocalUser`
- `modifier` → `LocalUser`

---

## `imr_snapshots`

Snapshots of the IMR state at a point in time. Used for versioning and comparison.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | UUID | PK | `uuid4` | Primary key |
| `tenant_id` | UUID | NOT NULL, FK → `app_tenants.id` | — | Tenant (CASCADE DELETE, INDEX) |
| `protection_mode_selection_id` | UUID | YES, FK → `protectionmode_selections.id` | — | Protection mode selection at snapshot time (SET NULL on delete, INDEX) |
| `label` | VARCHAR(255) | NOT NULL | — | Snapshot label/name |
| `description` | TEXT | YES | — | Description |
| `is_current` | BOOLEAN | NOT NULL | `False` | Whether this is the current snapshot |
| `item_count` | INTEGER | NOT NULL | `0` | Number of IMR items in this snapshot |
| `created_by` | UUID | YES, FK → `local_users.id` | — | Who created this snapshot (SET NULL on delete) |
| `created_at` | TIMESTAMP WITH TZ | YES | `now()` | Creation timestamp |
| `restored_from` | UUID | YES | — | If this snapshot was restored from another |

**Relationships:**
- `tenant` → `AppTenant`
- `protection_mode_selection` → `ProtectionModeSelection`
- `creator` → `LocalUser`
- `imr_items` → `ImrItem`

---

## `implementation_plan_items`

Legacy IMR implementation items (from v1). Being superseded by `imr_items`.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | UUID | PK | `uuid4` | Primary key |
| `tenant_id` | UUID | NOT NULL, FK → `app_tenants.id` | — | Tenant (INDEX) |
| `measure_id` | UUID | NOT NULL, FK → `eits_measures.id` | — | E-ITS measure |
| `target_type` | VARCHAR(50) | NOT NULL | — | Target object type |
| `target_id` | UUID | NOT NULL | — | Target object ID |
| `owner_user_id` | UUID | YES, FK → `users.id` | — | Owner (legacy users) |
| `status` | VARCHAR(50) | YES | `'not_started'` | Status |
| `priority` | VARCHAR(20) | YES | `'medium'` | Priority |
| `due_date` | TIMESTAMP | YES | — | Due date |
| `implementation_comment` | TEXT | YES | — | Implementation notes |
| `verification_method` | TEXT | YES | — | How to verify |
| `accepted_risk_id` | UUID | YES | — | Related risk acceptance |
| `created_at` | TIMESTAMP | YES | `now()` | Creation timestamp |
| `updated_at` | TIMESTAMP | YES | `now()` | Last update timestamp |

**Relationships:**
- `measure` → `EitsMeasure`
- `owner_user` → `User` (legacy)
