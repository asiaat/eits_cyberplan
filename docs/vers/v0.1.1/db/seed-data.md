# Seed Data Reference

This document documents all data that is seeded into the database on first startup or via `make seed`.

---

## Default Tenant

Created by `init_db.py` on first run.

| Field | Value |
|-------|-------|
| name | `"Default"` |
| status | `"active"` |
| plan | `"enterprise"` |

A legacy `Tenant` record is also created in sync.

---

## Permissions (33 records)

Seeded in `init_db.py`. 11 categories:

| # | Code | Category |
|---|------|----------|
| 1 | `users:read` | users |
| 2 | `users:write` | users |
| 3 | `roles:read` | users |
| 4 | `roles:write` | users |
| 5 | `processes:read` | processes |
| 6 | `processes:write` | processes |
| 7 | `assets:read` | assets |
| 8 | `assets:write` | assets |
| 9 | `risks:read` | risks |
| 10 | `risks:write` | risks |
| 11 | `evidence:read` | evidence |
| 12 | `evidence:write` | evidence |
| 13 | `evidence:upload` | evidence |
| 14 | `implementation:read` | implementation |
| 15 | `implementation:write` | implementation |
| 16 | `implementation:generate` | implementation |
| 17 | `dashboard:read` | dashboard |
| 18 | `catalog:read` | catalog |
| 19 | `catalog:import` | catalog |
| 20 | `audit:read` | audit |
| 21 | `audit:export` | audit |
| 22 | `organizations:read` | organizations |
| 23 | `organizations:write` | organizations |
| 24 | `people:read` | people |
| 25 | `people:write` | people |
| 26 | `protection_need:read` | protection_need |
| 27 | `protection_need:write` | protection_need |
| 28 | `damage_assessment:read` | damage_assessment |
| 29 | `damage_assessment:write` | damage_assessment |
| 30 | `mapping:read` | mapping |
| 31 | `mapping:write` | mapping |
| 32 | `imr_snapshot:create` | imr_snapshot |
| 33 | `settings:read` | settings |

---

## Default E-ITS Roles (per tenant)

Seeded in `init_db.py`. Each new tenant gets these 5 roles:

| # | Role Name | Description |
|---|-----------|-------------|
| 1 | `admin` | System Administrator — full access |
| 2 | `ism` | Information Security Manager — full access except catalog import and audit export |
| 3 | `process_owner` | Process Owner — read/write processes, read-only on risks/assets/evidence |
| 4 | `asset_owner` | Asset Owner — read/write assets, read-only on risks/evidence |
| 5 | `auditor` | Auditor — read-only on all entities |

### Role-Permission Mapping

| Permission | admin | ism | process_owner | asset_owner | auditor |
|------------|:-----:|:---:|:-------------:|:-----------:|:-------:|
| users:read | ✓ | ✓ | | | |
| users:write | ✓ | | | | |
| roles:read | ✓ | ✓ | | | |
| roles:write | ✓ | | | | |
| processes:read | ✓ | ✓ | ✓ | ✓ | ✓ |
| processes:write | ✓ | ✓ | ✓ | | |
| assets:read | ✓ | ✓ | ✓ | ✓ | ✓ |
| assets:write | ✓ | ✓ | | ✓ | |
| risks:read | ✓ | ✓ | ✓ | ✓ | ✓ |
| risks:write | ✓ | ✓ | | | |
| evidence:read | ✓ | ✓ | ✓ | ✓ | ✓ |
| evidence:write | ✓ | ✓ | | ✓ | |
| evidence:upload | ✓ | ✓ | ✓ | ✓ | |
| implementation:read | ✓ | ✓ | ✓ | ✓ | ✓ |
| implementation:write | ✓ | ✓ | ✓ | ✓ | |
| implementation:generate | ✓ | ✓ | | | |
| dashboard:read | ✓ | ✓ | ✓ | ✓ | ✓ |
| catalog:read | ✓ | ✓ | ✓ | ✓ | ✓ |
| catalog:import | ✓ | | | | |
| audit:read | ✓ | ✓ | ✓ | ✓ | ✓ |
| audit:export | ✓ | | | | |
| organizations:read | ✓ | ✓ | | | |
| organizations:write | ✓ | | | | |
| people:read | ✓ | ✓ | | | |
| people:write | ✓ | | | | |
| protection_need:read | ✓ | ✓ | ✓ | | |
| protection_need:write | ✓ | ✓ | | | |
| damage_assessment:read | ✓ | ✓ | ✓ | | |
| damage_assessment:write | ✓ | ✓ | | | |
| mapping:read | ✓ | ✓ | ✓ | ✓ | |
| mapping:write | ✓ | ✓ | | ✓ | |
| imr_snapshot:create | ✓ | ✓ | | | |
| settings:read | ✓ | ✓ | | | |

---

## Default Admin User

| Field | Value |
|-------|-------|
| email | `admin@eits.ee` |
| password | `admin123` |
| Local user name | `System Administrator` |

Created by `init_db.py` on first run. Seeded into both `global_users` and legacy `users`.

---

## Legacy Seed Roles (from migration `v2_iam_initial`)

| Code | Name |
|------|------|
| `infoturbejuht` | Information Security Manager (ISO) |
| `it_talitus` | IT Department |
| `juhtkond` | Management |

---

## Damage Scenarios (6 records, from migration)

| Code | Name |
|------|------|
| `KS1` | Legal/regulatory breach |
| `KS2` | Informational self-determination breach |
| `KS3` | Physical harm |
| `KS4` | Task performance impairment |
| `KS5` | Negative internal/external effects |
| `KS6` | Financial consequences |

---

## Asset Type Categories (5 records, from migration)

| Code | Name | Description |
|------|------|-------------|
| `T` | Infrastructure | Basic infrastructure |
| `V` | Network components | Network components |
| `I` | IT systems | IT systems |
| `R` | Applications | Applications |
| `A` | Industrial automation | Industrial automation systems |

---

## Asset Relation Types (8 records, from migration)

| Code | Name | Bidirectional | Strength |
|------|------|:------------:|:--------:|
| `runs_on` | Runs On | No | strong |
| `located_in` | Located In | No | weak |
| `connected_to` | Connected To | Yes | weak |
| `stores` | Stores | No | strong |
| `uses_service` | Uses Service | No | weak |
| `depends_on` | Depends On | No | weak |
| `supports` | Supports | Yes | weak |
| `contains` | Contains | Yes | strong |
