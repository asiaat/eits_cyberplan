# E-ITS Catalog

Tables for the E-ITS catalog reference data. Catalog versions are immutable after activation.

---

## `eits_catalog_versions`

Represents a versioned E-ITS catalog release.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | UUID | PK | `uuid4` | Primary key |
| `version` | VARCHAR(50) | NOT NULL | — | Version string |
| `year` | VARCHAR(4) | YES | — | Release year (INDEX) |
| `name` | VARCHAR(100) | YES | — | Version name |
| `source_name` | VARCHAR(255) | YES | — | Source file name |
| `source_file_hash` | VARCHAR(64) | YES | — | SHA-256 hash of source file |
| `imported_at` | TIMESTAMP | YES | `now()` | Import timestamp |
| `active` | BOOLEAN | YES | `False` | Whether version is active |
| `is_active` | BOOLEAN | YES | `False` | Active flag (INDEX) |
| `released_at` | DATE | YES | — | Official release date |

**Relationships:**
- `modules` → `EitsModule`
- `measures` → `EitsMeasure`
- `threats` → `EitsThreat`
- `security_profiles` → `SecurityProfile`
- `protectionmode_selections` → `ProtectionModeSelection`

---

## `eits_modules`

E-ITS security modules (baseline modules).

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | UUID | PK | `uuid4` | Primary key |
| `catalog_version_id` | UUID | NOT NULL, FK → `eits_catalog_versions.id` | — | Catalog version (INDEX) |
| `code` | VARCHAR(50) | NOT NULL | — | Module code (e.g., `ISMS`, `ORP`, `CON`) |
| `name` | VARCHAR(255) | NOT NULL | — | Module name |
| `module_group` | VARCHAR(10) | YES | — | Group identifier (INDEX) |
| `category` | VARCHAR(100) | YES | — | Category |
| `description` | TEXT | YES | — | Description |
| `module_type` | VARCHAR(50) | YES | — | `PROCESS` or `SYSTEM` |
| `source_url` | VARCHAR(500) | YES | — | Reference URL |

**Computed Properties:**
- `is_process_module`: True if `module_type == "PROCESS"` or `module_group in (ISMS, ORP, CON, OPS, DER)`
- `is_system_module`: True if `module_type == "SYSTEM"` or `module_group in (INF, NET, SYS, APP, IND)`

**Relationships:**
- `catalog_version` → `EitsCatalogVersion`
- `measures` → `EitsModuleMeasure` (junction to measures)
- `mappings` → `ObjectModuleMapping`
- `catalog_measures` → `EitsCatalogMeasure`
- `module_threats` → `ModuleThreat`
- `process_module_assignments` → `ProcessModuleAssignment`

---

## `eits_measures`

Legacy E-ITS measures (being superseded by `eits_catalog_measures`).

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | UUID | PK | `uuid4` | Primary key |
| `catalog_version_id` | UUID | NOT NULL, FK → `eits_catalog_versions.id` | — | Catalog version |
| `code` | VARCHAR(50) | NOT NULL | — | Measure code |
| `title` | VARCHAR(255) | NOT NULL | — | Measure title |
| `description` | TEXT | YES | — | Description |
| `measure_level` | VARCHAR(50) | YES | — | Level (`BASE`, `STANDARD`, `HIGH`) |
| `responsible_role` | VARCHAR(100) | YES | — | Responsible role description |
| `implementation_guidance` | TEXT | YES | — | Implementation guidance |

**Relationships:**
- `catalog_version` → `EitsCatalogVersion`
- `modules` → `EitsModuleMeasure` (junction)
- `implementation_items` → `ImplementationPlanItem`

---

## `eits_module_measures`

Junction table linking modules to their measures.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | UUID | PK | `uuid4` | Primary key |
| `module_id` | UUID | NOT NULL, FK → `eits_modules.id` | — | Module |
| `measure_id` | UUID | NOT NULL, FK → `eits_measures.id` | — | Measure |

**Relationships:**
- `module` → `EitsModule`
- `measure` → `EitsMeasure`

---

## `eits_catalog_measures`

New E-ITS catalog measures (v2). Connected directly to modules, with level classification.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | UUID | PK | `uuid4` | Primary key |
| `module_id` | UUID | NOT NULL, FK → `eits_modules.id` | — | Module (CASCADE DELETE, INDEX) |
| `code` | VARCHAR(30) | NOT NULL | — | Measure code (e.g., `ISMS.1`) |
| `name` | VARCHAR(255) | NOT NULL | — | Measure name |
| `measure_level` | VARCHAR(10) | NOT NULL | — | CHECK `IN ('BASE', 'STANDARD', 'HIGH')` (INDEX) |
| `description` | TEXT | YES | — | Description |
| `responsible_role` | VARCHAR(100) | YES | — | Responsible role |

**Unique Constraints:** `(module_id, code)` → `uq_eits_catalog_measures_module_code`

**Relationships:**
- `module` → `EitsModule`
- `imr_items` → `ImrItem`
- `risk_measure_links` → `RiskMeasureLink`
