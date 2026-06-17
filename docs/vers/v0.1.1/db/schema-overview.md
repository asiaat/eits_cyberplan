# Database Schema Overview

## Architecture: 3-Tier Design

The database is organized into three logical tiers plus a legacy layer that is being phased out.

### Tier A — Subscription Layer (Cross-Tenant)

Tables that manage tenant subscriptions and global user identities. These are the only tables that are **not** tenant-scoped (no `tenant_id`).

```
app_tenants ──1:N── tenant_users ──N:1── global_users
```

| Table | Purpose |
|-------|---------|
| `app_tenants` | Tenant/organization registry with contact info, divisions |
| `global_users` | Global user identities (email, password hash, MFA) |
| `tenant_users` | Junction: which users have access to which tenants |

### Tier B — Per-Tenant IAM

Each tenant has its own user profiles, roles, and role-permission assignments. All tables have `tenant_id` FK to `app_tenants`.

```
local_users ──1:N── user_roles ──N:1── e_its_roles ──N:N── e_its_role_permissions ──N:1── permissions
```

| Table | Purpose |
|-------|---------|
| `local_users` | Per-tenant user profiles (name, department, active status) |
| `e_its_roles` | Per-tenant role definitions (admin, ism, process_owner, asset_owner, auditor) |
| `user_roles` | Junction: which roles are assigned to which users (with audit trail for who granted) |
| `e_its_role_permissions` | Junction: which permissions each role has |

### Core Business Tables (Per-Tenant)

These tables hold the actual E-ITS domain data. Every table has `tenant_id` for isolation.

#### Business Processes & Assets
```
business_processes ──1:N── process_assets ──N:1── assets
business_processes ──1:N── business_process_dependencies
assets ──1:N── asset_relations → assets (self-ref)
```

#### E-ITS Catalog (Reference Data)
```
eits_catalog_versions ──1:N── eits_modules ──1:N── eits_module_measures ──N:1── eits_measures
                          └──1:N── eits_catalog_measures
                          └──1:N── eits_threats ──1:N── module_threats ──N:1── eits_modules
                          └──1:N── damage_scenarios
```

#### Module Mappings
```
assets ──1:N── asset_module_mappings ──N:1── eits_modules
business_processes ──1:N── bp_module_mappings ──N:1── eits_modules
object_module_mappings (polymorphic: target_type + target_id)
process_module_assignments ──N:1── eits_modules (per-tenant module applicability)
```

#### IMR (Implementation Plan)
```
asset_module_mappings ──1:N── imr_items ──N:1── eits_catalog_measures
bp_module_mappings ──1:N── imr_items
imr_snapshots ──1:N── imr_items
implementation_plan_items (legacy IMR implementation)
```

#### Risk Register
```
risks ──1:N── risk_measure_links ──N:1── imr_items
```

#### Evidence
```
evidences ──1:N── evidence_links (polymorphic: target_type + target_id)
```

#### Supporting
```
audit_logs (tenant-scoped audit trail)
comments (polymorphic entity comments)
persons ──1:N── person_organizations ──N:1── app_tenants
organization_people
alerts (tenant-scoped notifications)
damage_assessments ── app_tenants, business_processes, damage_scenarios
protection_need_summaries ── business_processes
security_profiles ── app_tenants, eits_catalog_versions
protectionmode_selections ── app_tenants, eits_catalog_versions
damage_category_thresholds ── app_tenants, damage_scenarios
asset_type_categories (reference data)
```

### Legacy Tables (In Migration)

These tables are the original implementation and are gradually being replaced by Tier A/B equivalents.

| Legacy | Replacement |
|--------|-------------|
| `tenants` | `app_tenants` (Tier A) |
| `users` | `global_users` + `local_users` (Tier A + B) |
| `roles` | `e_its_roles` (Tier B) |
| `permissions` | Same table (shared) |
| `role_permissions` | `e_its_role_permissions` (Tier B) |
| `memberships` | `user_roles` + `tenant_users` (Tier A + B) |

## Design Patterns

### Soft Delete
9 tables use `SoftDeleteMixin` which adds:
- `deleted_at` — timestamp of deletion (nullable, indexed)
- `deleted_by` — UUID of the actor (nullable)

Tables: `assets`, `business_processes`, `risks`, `evidences`, `imr_items`, `damage_assessments`, `protectionmode_selections`, `security_profiles`, `persons`

### Tenant Isolation
Every business-logic table has `tenant_id UUID NOT NULL REFERENCES app_tenants(id) ON DELETE CASCADE`. All queries must filter by tenant.

### Generated Columns
- `risks.risk_score` = `likelihood_score * impact_score` (GENERATED ALWAYS AS STORED)

### Database Triggers
- `asset_relations`: `BEFORE INSERT/UPDATE` — prevents circular dependencies via recursive CTE
- `damage_assessments`: `BEFORE INSERT OR UPDATE` — auto-calculates `damage_category` as `GREATEST(availability_impact, confidentiality_impact, integrity_impact)`

## Enum-Like Values

Protection Need: `NORMAL`, `HIGH`, `VERY_HIGH`
PEARO Status: `P` (Not Applicable), `E` (Not Implemented), `A` (Accepted Risk), `R` (Implemented), `O` (Partially Implemented)
Security Approach: `BASIC`, `STANDARD`, `CORE`
Asset Categories: `T` (Infrastructure), `V` (Network), `I` (IT Systems), `R` (Applications), `A` (Industrial Automation)
Risk Treatment: `MITIGATE`, `ACCEPT`, `TRANSFER`, `AVOID`
