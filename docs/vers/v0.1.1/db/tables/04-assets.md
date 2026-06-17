# Assets

Tables for asset register, asset-to-asset relationships, and relation type definitions.

---

## `assets`

Represents an information asset within a tenant. Supports soft delete.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | UUID | PK | `uuid4` | Primary key |
| `tenant_id` | UUID | NOT NULL, FK → `app_tenants.id` | — | Tenant (INDEX) |
| `owner_user_id` | UUID | YES, FK → `users.id` | — | Asset owner (legacy users) |
| `person_id` | UUID | YES, FK → `persons.id` | — | Responsible person (INDEX, RESTRICT on delete) |
| `name` | VARCHAR(255) | NOT NULL | — | Asset name |
| `asset_type` | VARCHAR(50) | NOT NULL | — | Type (`information_asset`, `software`, `hardware`, `service`, `data`, `competence`, `other`) |
| `description` | TEXT | YES | — | Description |
| `remarks` | TEXT | YES | — | Additional remarks |
| `criticality` | VARCHAR(20) | YES | `'normal'` | Criticality (`low`, `normal`, `high`, `critical`) |
| `confidentiality_need` | VARCHAR(20) | YES | `'normal'` | Confidentiality protection need |
| `integrity_need` | VARCHAR(20) | YES | `'normal'` | Integrity protection need |
| `availability_need` | VARCHAR(20) | YES | `'normal'` | Availability protection need |
| `lifecycle_status` | VARCHAR(50) | YES | `'active'` | Lifecycle (`active`, `inactive`, `deprecated`, `retired`) |
| `is_grouped` | BOOLEAN | NOT NULL | `false` | Whether this is a grouped/target object (server_default=`'false'`) |
| `quantity` | INTEGER | NOT NULL | `1` | Number of instances (server_default=`'1'`) |
| `group_name` | VARCHAR(255) | YES | — | Group name for grouped assets |
| `is_core` | BOOLEAN | NOT NULL | `false` | Core asset flag (server_default=`'false'`) |
| `asset_index` | VARCHAR(10) | YES | — | Asset index number |
| `asset_category` | VARCHAR(5) | YES | — | Category code (`T`, `V`, `I`, `R`, `A`) (INDEX, FK → `asset_type_categories.code`) |
| `location` | VARCHAR(255) | YES | — | Physical/virtual location |
| `protection_need` | VARCHAR(20) | YES | `'NORMAL'` | Overall protection need (`NORMAL`, `HIGH`, `VERY_HIGH`) |
| `protection_need_justification` | TEXT | YES | — | Justification for protection need |
| `protection_source_process_ids` | ARRAY(UUID) | YES | — | Source business process IDs that determined protection need |
| `created_at` | TIMESTAMP | YES | `now()` | Creation timestamp |
| `updated_at` | TIMESTAMP | YES | `now()` | Last update timestamp |
| `deleted_at` | TIMESTAMP | YES | — | Soft delete timestamp (INDEX) |
| `deleted_by` | UUID | YES | — | Who deleted this record |

**Soft Delete:** Yes

**Protection Need Values:** `NORMAL`, `HIGH`, `VERY_HIGH`

**Relationships:**
- `owner_user` → `User` (legacy)
- `person` → `Person`
- `relations_from` → `AssetRelation` (as source)
- `relations_to` → `AssetRelation` (as target)
- `processes` → `ProcessAsset` (linked business processes)
- `module_mappings` → `AssetModuleMapping` (mapped E-ITS modules, cascade delete)

---

## `asset_relations`

Tracks relationships between assets. Has DB triggers to prevent circular dependencies.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | UUID | PK | `uuid4` | Primary key |
| `tenant_id` | UUID | NOT NULL, FK → `app_tenants.id` | — | Tenant (INDEX) |
| `source_asset_id` | UUID | NOT NULL, FK → `assets.id` | — | Source asset (depends on) |
| `target_asset_id` | UUID | NOT NULL, FK → `assets.id` | — | Target asset (depended upon) |
| `relation_type` | VARCHAR(50) | NOT NULL | — | Legacy relation type |
| `relation_type_code` | VARCHAR(50) | YES, FK → `asset_relation_types.code` | — | Reference to relation type definition |
| `description` | TEXT | YES | — | Description of relationship |
| `bidirectional` | BOOLEAN | YES | `False` | Whether relationship is bidirectional |
| `strength` | VARCHAR(20) | YES | `'weak'` | Relationship strength |
| `created_at` | TIMESTAMP | YES | `now()` | Creation timestamp |

**DB Triggers:**
- `check_asset_relation_circular_insert` — BEFORE INSERT, prevents circular dependencies
- `check_asset_relation_circular_update` — BEFORE UPDATE OF `target_asset_id`, prevents circular dependencies

**Relationships:**
- `source_asset` → `Asset`
- `target_asset` → `Asset`
- `relation_type_info` → `AssetRelationType`

---

## `asset_relation_types`

Defines valid relation types between assets.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | UUID | PK | `uuid4` | Primary key |
| `code` | VARCHAR(50) | NOT NULL | — | Relation code (UNIQUE, INDEX) |
| `name` | VARCHAR(255) | NOT NULL | — | Display name |
| `description` | TEXT | YES | — | Description |
| `source_types` | VARCHAR(500) | YES | — | JSON array of valid source asset types |
| `target_types` | VARCHAR(500) | YES | — | JSON array of valid target asset types |
| `bidirectional` | BOOLEAN | YES | `False` | Whether this is a bidirectional relation |
| `strength` | VARCHAR(20) | YES | `'weak'` | Default strength |
| `created_at` | TIMESTAMP | YES | `now()` | Creation timestamp |

**Seed Data (8 types):**

| Code | Name | Description |
|------|------|-------------|
| `runs_on` | Runs On | Asset runs on another asset |
| `located_in` | Located In | Asset is physically located in |
| `connected_to` | Connected To | Network/connectivity relation |
| `stores` | Stores | Asset stores data in |
| `uses_service` | Uses Service | Asset consumes a service |
| `depends_on` | Depends On | Dependency relationship |
| `supports` | Supports | Asset supports another |
| `contains` | Contains | Asset contains another |

**Relationships:**
- `relations` → `AssetRelation` (via `relation_type_code`)
