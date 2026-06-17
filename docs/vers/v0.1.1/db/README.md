# E-ITS Management System — Database Documentation v0.1.1

This directory contains the complete database documentation for the E-ITS Management System.

## Architecture Overview

The database uses a **3-tier architecture**:

| Tier | Scope | Tables | Description |
|------|-------|--------|-------------|
| **Tier A** | Cross-tenant | `app_tenants`, `global_users`, `tenant_users` | Subscription and identity layer — shared across all tenants |
| **Tier B** | Per-tenant | ~15 tenant-scoped tables | Each tenant's data isolated by `tenant_id` foreign key |
| **Core** | Per-tenant | ~25 business tables | Core domain entities with `tenant_id` on every row |

Additionally, **Legacy** tables (`tenants`, `users`, `roles`, `permissions`, `role_permissions`, `memberships`) exist alongside the Tier A/B equivalents and are being gradually migrated away.

## Key Design Principles

- **Tenant isolation** — every tenant-scoped table has a `tenant_id` column with FK to `app_tenants`
- **Soft delete** — 9 tables use `SoftDeleteMixin` (`deleted_at`, `deleted_by`)
- **Audit logging** — all important writes are recorded in `audit_logs`
- **Catalog versioning** — E-ITS catalog versions are immutable after activation
- **PEARO lifecycle** — IMR items track status through Plan → Evaluate → Accept → Realize → Operate
- **Generated columns** — `risks.risk_score` is computed as `likelihood_score * impact_score`
- **DB triggers** — circular dependency prevention on `asset_relations`, auto-calculation of `damage_category`

## File Structure

| File | Content |
|------|---------|
| `schema-overview.md` | High-level schema design with tier breakdown |
| `erd.md` | Entity-relationship descriptions |
| `tables/01-tier-a-subscription.md` | Subscription layer (Tier A) |
| `tables/02-tier-b-iam.md` | Per-tenant IAM (Tier B) |
| `tables/03-business-processes.md` | Business processes and dependencies |
| `tables/04-assets.md` | Assets and asset relations |
| `tables/05-catalog.md` | E-ITS catalog (versions, modules, measures) |
| `tables/06-threats-damage.md` | Threats, damage scenarios, assessments |
| `tables/07-mappings.md` | Module mappings, security profiles |
| `tables/08-imr.md` | IMR items, snapshots |
| `tables/09-risk.md` | Risk register |
| `tables/10-evidence.md` | Evidence management |
| `tables/11-supporting.md` | Audit log, comments, persons, alerts |
| `tables/12-legacy.md` | Legacy tables being migrated |
| `migration-history.md` | Alembic migration changelog |
| `seed-data.md` | All default seed data |
| `data-dictionary.md` | Flat column reference across all tables |
| `indexes-constraints.md` | All constraints, indexes, triggers |
| `views.md` | Database views |

## Total Tables: 50
