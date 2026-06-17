# Threats and Damage Assessment

Tables for E-ITS threat catalog, damage scenarios, and business process damage assessments.

---

## `eits_threats`

E-ITS threat catalog entries, versioned per catalog version.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | UUID | PK | `uuid4` | Primary key |
| `version_id` | UUID | NOT NULL, FK → `eits_catalog_versions.id` | — | Catalog version (CASCADE DELETE, INDEX) |
| `code` | VARCHAR(30) | NOT NULL | — | Threat code |
| `category` | VARCHAR(100) | YES | — | Threat category |
| `impact_area` | VARCHAR(100) | YES | — | Affected impact area |
| `name` | VARCHAR(255) | NOT NULL | — | Threat name |
| `description` | TEXT | YES | — | Description |

**Unique Constraints:** `(version_id, code)` → `uq_eits_threats_version_code`

**Relationships:**
- `version` → `EitsCatalogVersion`
- `module_threats` → `ModuleThreat`

---

## `module_threats`

Junction table linking modules to relevant threats.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | UUID | PK | `uuid4` | Primary key |
| `module_id` | UUID | NOT NULL, FK → `eits_modules.id` | — | Module (CASCADE DELETE) |
| `threat_id` | UUID | NOT NULL, FK → `eits_threats.id` | — | Threat (CASCADE DELETE) |
| `relevance_note` | TEXT | YES | — | Note on relevance to this module |

**Unique Constraints:** `(module_id, threat_id)` → `uq_module_threats`

**Relationships:**
- `module` → `EitsModule`
- `threat` → `EitsThreat`

---

## `damage_scenarios`

Fixed set of 6 standard damage scenarios (KS1–KS6) defined by E-ITS methodology.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | UUID | PK | `uuid4` | Primary key |
| `code` | VARCHAR(10) | NOT NULL | — | Scenario code (UNIQUE) |
| `name` | VARCHAR(255) | NOT NULL | — | Scenario name |
| `description` | TEXT | YES | — | Description |

**Seed Data:**

| Code | Name |
|------|------|
| `KS1` | Legal/regulatory breach |
| `KS2` | Informational self-determination breach |
| `KS3` | Physical harm |
| `KS4` | Task performance impairment |
| `KS5` | Negative internal/external effects |
| `KS6` | Financial consequences |

---

## `damage_assessments`

Per-business-process assessment of damage impact across KS1–KS6 scenarios. Supports soft delete.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | UUID | PK | `uuid4` | Primary key |
| `tenant_id` | UUID | NOT NULL, FK → `app_tenants.id` | — | Tenant (CASCADE DELETE) |
| `business_process_id` | UUID | NOT NULL, FK → `business_processes.id` | — | Business process (CASCADE DELETE, INDEX) |
| `damage_scenario_id` | UUID | NOT NULL, FK → `damage_scenarios.id` | — | Damage scenario |
| `availability_impact` | INTEGER | YES | `0` | CHECK `BETWEEN 0 AND 3` |
| `confidentiality_impact` | INTEGER | YES | `0` | CHECK `BETWEEN 0 AND 3` |
| `integrity_impact` | INTEGER | YES | `0` | CHECK `BETWEEN 0 AND 3` |
| `damage_category` | INTEGER | YES | — | Auto-calculated: `GREATEST(availability, confidentiality, integrity)` |
| `justification` | TEXT | YES | — | Justification for assessment |
| `assessed_by` | UUID | YES, FK → `local_users.id` | — | Who performed the assessment (SET NULL on delete) |
| `assessed_at` | TIMESTAMP WITH TZ | YES | `now()` | When assessed |

**Unique Constraints:** `(tenant_id, business_process_id, damage_scenario_id)` → `uq_damage_assessment`

**DB Trigger:** `trg_damage_assessment_damage_category` — BEFORE INSERT OR UPDATE, auto-calculates `damage_category = GREATEST(availability_impact, confidentiality_impact, integrity_impact)`

**Relationships:**
- `tenant` → `AppTenant`
- `business_process` → `BusinessProcess`
- `damage_scenario` → `DamageScenario`
- `assessed_by_user` → `LocalUser`

---

## `damage_category_thresholds`

Tenant-specific threshold descriptions for each damage scenario's impact levels.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | UUID | PK | `uuid4` | Primary key |
| `tenant_id` | UUID | NOT NULL, FK → `app_tenants.id` | — | Tenant (CASCADE DELETE) |
| `damage_scenario_id` | UUID | NOT NULL, FK → `damage_scenarios.id` | — | Damage scenario (CASCADE DELETE) |
| `negligible_description` | TEXT | YES | — | Description of level 0 (negligible) |
| `limited_description` | TEXT | YES | — | Description of level 1 (limited) |
| `serious_description` | TEXT | YES | — | Description of level 2 (serious) |
| `catastrophic_description` | TEXT | YES | — | Description of level 3 (catastrophic) |
| `approved_by` | UUID | YES, FK → `local_users.id` | — | Who approved these thresholds (SET NULL on delete) |
| `created_at` | TIMESTAMP WITH TZ | YES | `now()` | Creation timestamp |
| `updated_at` | TIMESTAMP WITH TZ | YES | `now()` | Last update timestamp |

**Unique Constraints:** `(tenant_id, damage_scenario_id)` → `uq_damage_threshold`

**Relationships:**
- `tenant` → `AppTenant`
- `damage_scenario` → `DamageScenario`
- `approved_by_user` → `LocalUser`
