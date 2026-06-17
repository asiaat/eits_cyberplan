# Database Views

The database includes several views for reporting and data analysis.

---

## `v_imr_summary`

IMR item counts grouped by tenant, PEARO status, and measure level, with overdue counts.

**Purpose:** Dashboard and reporting — provides IMR implementation progress at a glance.

**Source:** Migration `v3_eits_tier_ab_full`

**Columns:**
| Column | Type | Description |
|--------|------|-------------|
| `tenant_id` | UUID | Tenant |
| `pearo_status` | VARCHAR(1) | PEARO status (P/E/A/R/O) |
| `measure_level` | VARCHAR(10) | Measure level (BASE/STANDARD/HIGH) |
| `item_count` | INTEGER | Number of IMR items in this group |
| `overdue_count` | INTEGER | Number of items past due date |

**Joins:** `imr_items` → `eits_catalog_measures` (for `measure_level`) → `app_tenants`

**Aggregation:** Grouped by `(tenant_id, pearo_status, measure_level)`

---

## `v_risk_matrix`

Risk count matrix grouped by impact and likelihood scores.

**Purpose:** Risk heatmap visualization — shows count of risks at each (impact, likelihood) intersection.

**Source:** Migration `v3_eits_tier_ab_full`

**Columns:**
| Column | Type | Description |
|--------|------|-------------|
| `tenant_id` | UUID | Tenant |
| `impact_score` | INTEGER | Impact score (0–3) |
| `likelihood_score` | INTEGER | Likelihood score (0–3) |
| `risk_count` | INTEGER | Number of risks at this intersection |

**Aggregation:** Grouped by `(tenant_id, impact_score, likelihood_score)`

---

## `v_asset_protection_overview`

Asset protection overview with mapped module counts, IMR item counts, and implementation status.

**Purpose:** Asset-focused dashboard — shows protection status, modeling progress, and implementation gaps.

**Source:** Migration `v3_eits_tier_ab_full`

**Columns:**
| Column | Type | Description |
|--------|------|-------------|
| `tenant_id` | UUID | Tenant |
| `asset_id` | UUID | Asset |
| `asset_name` | VARCHAR | Asset name |
| `asset_type` | VARCHAR | Asset type |
| `protection_need` | VARCHAR | Current protection need |
| `mapped_module_count` | INTEGER | Number of E-ITS modules mapped |
| `total_imr_items` | INTEGER | Total IMR items |
| `implemented_imr_items` | INTEGER | IMR items with PEARO status 'R' (Implemented) |
| `overdue_imr_items` | INTEGER | IMR items past due date |
| `evidence_count` | INTEGER | Evidence linked via evidence_links |

---

## `v_asset_protection_inheritance`

Recursive CTE view that propagates protection needs through asset relations.

**Purpose:** Calculates inherited protection needs — when an asset's protection need should flow through `runs_on`, `located_in`, `contains`, `depends_on`, and `supports` relations to connected assets.

**Source:** Migration `add_asset_relation_types_v1`

**Key Logic (Recursive CTE):**
1. Start with assets that have explicit protection needs from business process linkage
2. Traverse asset relations following the chain
3. Propagate the maximum protection need along each path
4. Handle both directions for bidirectional relation types

**Columns:**
| Column | Type | Description |
|--------|------|-------------|
| `tenant_id` | UUID | Tenant |
| `source_asset_id` | UUID | Asset where protection originates |
| `source_asset_name` | VARCHAR | Source asset name |
| `related_asset_id` | UUID | Asset that inherits protection need |
| `related_asset_name` | VARCHAR | Inheriting asset name |
| `relation_type_code` | VARCHAR | Type of relation |
| `inherited_confidentiality_need` | VARCHAR | Inherited confidentiality need |
| `inherited_integrity_need` | VARCHAR | Inherited integrity need |
| `inherited_availability_need` | VARCHAR | Inherited availability need |
| `inherited_protection_need` | VARCHAR | Overall inherited protection need |
| `inheritance_depth` | INTEGER | How many hops from the source |
| `inheritance_path` | TEXT | Path of asset IDs through the relation chain |
