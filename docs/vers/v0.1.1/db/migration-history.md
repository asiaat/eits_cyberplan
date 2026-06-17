# Migration History

This file documents the Alembic migration chain — what each migration adds or changes.

## Migration Versions

| # | Version | Name | Description |
|---|---------|------|-------------|
| 1 | `v1_initial_schema` | Initial Schema | Creates all core tables: `tenants`, `users`, `roles`, `permissions`, `role_permissions`, `memberships`, `business_processes`, `assets`, `asset_relations`, `process_assets`, `eits_catalog_versions`, `eits_modules`, `eits_measures`, `eits_module_measures`, `object_module_mappings`, `implementation_plan_items`, `risks`, `evidences`, `evidence_links`, `audit_logs`, `comments` |
| 2 | `v2_iam_initial` | IAM Initial | Adds legacy seed roles (`infoturbejuht`, `it_talitus`, `juhtkond`). Seeds damage scenarios KS1–KS6 and asset type categories (T/V/I/R/A) |
| 3 | `v3_eits_tier_ab_full` | E-ITS Tier A/B Full | Major expansion: Tier A (`app_tenants`, `global_users`, `tenant_users`), Tier B IAM (`local_users`, `e_its_roles`, `user_roles`, `e_its_role_permissions`), Tier A catalog entities (`eits_catalog_measures`, `eits_threats`, `module_threats`, `damage_scenarios`), Tier B entities (`security_profiles`, `damage_assessments`, `protection_need_summaries`, `asset_type_categories`, `asset_module_mappings`, `bp_module_mappings`, `imr_items`, `risk_measure_links`, `damage_category_thresholds`, `process_module_assignments`, `protectionmode_selections`, `imr_snapshots`). Adds triggers on `damage_assessments` and `asset_relations`. Creates views `v_imr_summary`, `v_risk_matrix`, `v_asset_protection_overview` |
| 4 | `add_asset_relation_types_v1` | Asset Relation Types | Adds `asset_relation_types` table and `belongs_to`, `supports` relations. Adds `v_asset_protection_inheritance` recursive CTE view. Adds `person_id`, `relation_type_code` to `asset_relations`. Enhances `assets` with `asset_index`, `asset_category`, `is_grouped`, `quantity`, `group_name`, `is_core`, `location`, `protection_need`, `protection_need_justification`, `protection_source_process_ids`, `remarks` |
| 5 | `v5_business_process_deps` | Business Process Dependencies | Adds `business_process_dependencies` table. Adds `process_type` and `priority` to `business_processes`. Adds `persons`, `person_organizations`, `organization_people`, `alerts` tables. Adds `confidentiality_need` to `damage_assessments` (added alongside existing `availability_impact`, `confidentiality_impact`, `integrity_impact`) |

> **Note:** Migration file names in the actual `alembic/versions/` directory use the format `{hash}_{name}.py`. The version names above are logical identifiers.
