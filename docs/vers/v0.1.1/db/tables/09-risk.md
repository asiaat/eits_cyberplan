# Risk Register

Tables for the risk register, risk assessment, and risk-measure relationships.

---

## `risks`

Risk register entries. Supports soft delete. Each risk describes a scenario with impact and likelihood assessment.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | UUID | PK | `uuid4` | Primary key |
| `tenant_id` | UUID | NOT NULL, FK → `app_tenants.id` | — | Tenant (INDEX) |
| `title` | VARCHAR(255) | NOT NULL | — | Risk title |
| `scenario` | TEXT | YES | — | Risk scenario description |
| `target_type` | VARCHAR(50) | YES | — | Related target object type |
| `target_id` | UUID | YES | — | Related target object ID |
| `threat` | TEXT | YES | — | Threat description |
| `vulnerability` | TEXT | YES | — | Vulnerability description |
| `likelihood` | VARCHAR(20) | YES | — | Legacy likelihood value |
| `impact` | VARCHAR(20) | YES | — | Legacy impact value |
| `risk_level` | VARCHAR(20) | YES | — | Legacy calculated risk level |
| `treatment` | VARCHAR(50) | YES | — | Legacy treatment selection |
| `owner_user_id` | UUID | YES, FK → `users.id` | — | Risk owner (legacy users) |
| `status` | VARCHAR(50) | YES | `'identified'` | Risk status |
| `review_date` | TIMESTAMP | YES | — | Next review date |
| `threat_id` | UUID | YES | — | FK to `eits_threats.id` (INDEX) |
| `asset_id` | UUID | YES | — | Related asset (INDEX) |
| `business_process_id` | UUID | YES | — | Related business process (INDEX) |
| `likelihood_score` | INTEGER | YES | — | Likelihood score 0–3 |
| `impact_score` | INTEGER | YES | — | Impact score 0–3 |
| `risk_score` | INTEGER | GENERATED | — | `likelihood_score * impact_score` (STORED) |
| `risk_rating` | VARCHAR(20) | YES | — | Risk rating label |
| `treatment_type` | VARCHAR(30) | YES | — | CHECK `IN ('MITIGATE', 'ACCEPT', 'TRANSFER', 'AVOID')` |
| `residual_risk_level` | VARCHAR(20) | YES | — | Residual risk after treatment |
| `accepted_by` | UUID | YES | — | Who accepted the risk |
| `accepted_at` | TIMESTAMP WITH TZ | YES | — | When risk was accepted |
| `created_at` | TIMESTAMP | YES | `now()` | Creation timestamp |
| `updated_at` | TIMESTAMP | YES | `now()` | Last update timestamp |
| `deleted_at` | TIMESTAMP | YES | — | Soft delete timestamp |
| `deleted_by` | UUID | YES | — | Who deleted this record |

**Soft Delete:** Yes

**Generated Column:** `risk_score` is computed as `likelihood_score * impact_score` (GENERATED ALWAYS AS STORED).

**Treatment Types:** `MITIGATE`, `ACCEPT`, `TRANSFER`, `AVOID`

**Relationships:**
- `owner_user` → `User` (legacy)
- `risk_measure_links` → `RiskMeasureLink`

---

## `risk_measure_links`

Junction table linking risks to IMR items and catalog measures.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | UUID | PK | `uuid4` | Primary key |
| `tenant_id` | UUID | NOT NULL, FK → `app_tenants.id` | — | Tenant (CASCADE DELETE) |
| `risk_id` | UUID | NOT NULL, FK → `risks.id` | — | Risk (CASCADE DELETE, INDEX) |
| `imr_item_id` | UUID | YES, FK → `imr_items.id` | — | Related IMR item (SET NULL on delete) |
| `measure_id` | UUID | YES, FK → `eits_catalog_measures.id` | — | Related catalog measure (SET NULL on delete) |
| `custom_measure_name` | VARCHAR(255) | YES | — | Custom measure name (for measures not in catalog) |
| `custom_measure_description` | TEXT | YES | — | Custom measure description |
| `created_at` | TIMESTAMP WITH TZ | YES | `now()` | Creation timestamp |

**Relationships:**
- `tenant` → `AppTenant`
- `risk` → `Risk`
- `imr_item` → `ImrItem`
- `measure` → `EitsCatalogMeasure`
