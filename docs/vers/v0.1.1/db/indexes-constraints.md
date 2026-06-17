# Indexes, Constraints, and Triggers

## Primary Keys

All 50 tables use UUID primary keys with `uuid4` generation, except:

| Table | PK Type |
|-------|---------|
| `roles` | TEXT |
| `permissions` | TEXT |
| `role_permissions` | Composite `(role_id, permission_id)` |
| `e_its_role_permissions` | Composite `(role_id, permission_id)` |
| `tenant_users` | Composite `(tenant_id, user_id)` |

## Unique Constraints

| Table | Columns | Constraint Name |
|-------|---------|-----------------|
| `tenants` | `registry_code` | — |
| `global_users` | `email` | — |
| `roles` | `code` | — |
| `permissions` | `code` | — |
| `local_users` | `(global_user_id, tenant_id)` | `uq_local_user_global_tenant` |
| `e_its_roles` | `(tenant_id, role_name)` | `uq_e_its_role_tenant` |
| `business_process_dependencies` | `(primary_process_id, depends_on_process_id)` | `uq_bp_dependency_pair` |
| `eits_catalog_measures` | `(module_id, code)` | `uq_eits_catalog_measures_module_code` |
| `eits_threats` | `(version_id, code)` | `uq_eits_threats_version_code` |
| `module_threats` | `(module_id, threat_id)` | `uq_module_threats` |
| `damage_scenarios` | `code` | — |
| `asset_type_categories` | `code` | — |
| `asset_relation_types` | `code` | — |
| `persons` | `national_id` | — |
| `person_organizations` | `(person_id, tenant_id)` | `uq_person_tenant` |
| `organization_people` | `(tenant_id, person_asset_id)` | `uq_org_person` |
| `damage_assessments` | `(tenant_id, business_process_id, damage_scenario_id)` | `uq_damage_assessment` |
| `protection_need_summaries` | `(tenant_id, business_process_id)` | `uq_protection_need_summary` |
| `asset_module_mappings` | `(tenant_id, asset_id, module_id)` | `uq_asset_module_mapping` |
| `bp_module_mappings` | `(tenant_id, business_process_id, module_id)` | `uq_bp_module_mapping` |
| `security_profiles` | `(tenant_id, catalog_version_id)` | `uq_security_profile_tenant_version` |
| `process_module_assignments` | `(tenant_id, module_id)` | `uq_process_module_assignment` |
| `damage_category_thresholds` | `(tenant_id, damage_scenario_id)` | `uq_damage_threshold` |

## Foreign Keys

### Tier A

| FK Column | Parent Table | Delete Rule |
|-----------|-------------|-------------|
| `tenant_users.tenant_id` | `app_tenants.id` | CASCADE |
| `tenant_users.user_id` | `global_users.id` | CASCADE |

### Tier B IAM

| FK Column | Parent Table | Delete Rule |
|-----------|-------------|-------------|
| `local_users.global_user_id` | `global_users.id` | CASCADE |
| `local_users.tenant_id` | `app_tenants.id` | CASCADE |
| `e_its_roles.tenant_id` | `app_tenants.id` | CASCADE |
| `user_roles.user_id` | `local_users.id` | CASCADE |
| `user_roles.role_id` | `e_its_roles.id` | CASCADE |
| `user_roles.granted_by` | `local_users.id` | SET NULL |
| `e_its_role_permissions.role_id` | `e_its_roles.id` | CASCADE |
| `e_its_role_permissions.permission_id` | `permissions.id` | CASCADE |

### Business Processes & Assets

| FK Column | Parent Table | Delete Rule |
|-----------|-------------|-------------|
| `business_processes.tenant_id` | `app_tenants.id` | — |
| `business_processes.owner_user_id` | `local_users.id` | SET NULL |
| `business_process_dependencies.tenant_id` | `app_tenants.id` | CASCADE |
| `business_process_dependencies.primary_process_id` | `business_processes.id` | CASCADE |
| `business_process_dependencies.depends_on_process_id` | `business_processes.id` | CASCADE |
| `process_assets.tenant_id` | `app_tenants.id` | — |
| `process_assets.business_process_id` | `business_processes.id` | — |
| `process_assets.asset_id` | `assets.id` | — |
| `assets.tenant_id` | `app_tenants.id` | — |
| `assets.owner_user_id` | `users.id` | — |
| `assets.person_id` | `persons.id` | RESTRICT |
| `asset_relations.tenant_id` | `app_tenants.id` | — |
| `asset_relations.source_asset_id` | `assets.id` | — |
| `asset_relations.target_asset_id` | `assets.id` | — |
| `asset_relations.relation_type_code` | `asset_relation_types.code` | — |

### E-ITS Catalog

| FK Column | Parent Table | Delete Rule |
|-----------|-------------|-------------|
| `eits_catalog_versions` | — | — (root table) |
| `eits_modules.catalog_version_id` | `eits_catalog_versions.id` | — |
| `eits_measures.catalog_version_id` | `eits_catalog_versions.id` | — |
| `eits_module_measures.module_id` | `eits_modules.id` | — |
| `eits_module_measures.measure_id` | `eits_measures.id` | — |
| `eits_catalog_measures.module_id` | `eits_modules.id` | CASCADE |
| `eits_threats.version_id` | `eits_catalog_versions.id` | CASCADE |
| `module_threats.module_id` | `eits_modules.id` | CASCADE |
| `module_threats.threat_id` | `eits_threats.id` | CASCADE |

### Mappings

| FK Column | Parent Table | Delete Rule |
|-----------|-------------|-------------|
| `object_module_mappings.tenant_id` | `app_tenants.id` | — |
| `object_module_mappings.module_id` | `eits_modules.id` | — |
| `object_module_mappings.selected_by_user_id` | `users.id` | — |
| `asset_module_mappings.tenant_id` | `app_tenants.id` | CASCADE |
| `asset_module_mappings.asset_id` | `assets.id` | CASCADE |
| `asset_module_mappings.module_id` | `eits_modules.id` | CASCADE |
| `asset_module_mappings.modeled_by` | `local_users.id` | SET NULL |
| `bp_module_mappings.tenant_id` | `app_tenants.id` | CASCADE |
| `bp_module_mappings.business_process_id` | `business_processes.id` | CASCADE |
| `bp_module_mappings.module_id` | `eits_modules.id` | CASCADE |
| `bp_module_mappings.modeled_by` | `local_users.id` | SET NULL |
| `process_module_assignments.tenant_id` | `app_tenants.id` | CASCADE |
| `process_module_assignments.module_id` | `eits_modules.id` | CASCADE |
| `process_module_assignments.assigned_by` | `local_users.id` | SET NULL |

### IMR

| FK Column | Parent Table | Delete Rule |
|-----------|-------------|-------------|
| `imr_items.tenant_id` | `app_tenants.id` | CASCADE |
| `imr_items.asset_module_mapping_id` | `asset_module_mappings.id` | CASCADE |
| `imr_items.bp_module_mapping_id` | `bp_module_mappings.id` | CASCADE |
| `imr_items.measure_id` | `eits_catalog_measures.id` | CASCADE |
| `imr_items.responsible_user_id` | `local_users.id` | SET NULL |
| `imr_items.risk_acceptance_approved_by` | `local_users.id` | SET NULL |
| `imr_items.imr_snapshot_id` | `imr_snapshots.id` | SET NULL |
| `imr_items.created_by` | `local_users.id` | SET NULL |
| `imr_items.updated_by` | `local_users.id` | SET NULL |
| `imr_snapshots.tenant_id` | `app_tenants.id` | CASCADE |
| `imr_snapshots.protection_mode_selection_id` | `protectionmode_selections.id` | SET NULL |
| `imr_snapshots.created_by` | `local_users.id` | SET NULL |
| `implementation_plan_items.tenant_id` | `app_tenants.id` | — |
| `implementation_plan_items.measure_id` | `eits_measures.id` | — |
| `implementation_plan_items.owner_user_id` | `users.id` | — |

### Risk

| FK Column | Parent Table | Delete Rule |
|-----------|-------------|-------------|
| `risks.tenant_id` | `app_tenants.id` | — |
| `risks.owner_user_id` | `users.id` | — |
| `risk_measure_links.tenant_id` | `app_tenants.id` | CASCADE |
| `risk_measure_links.risk_id` | `risks.id` | CASCADE |
| `risk_measure_links.imr_item_id` | `imr_items.id` | SET NULL |
| `risk_measure_links.measure_id` | `eits_catalog_measures.id` | SET NULL |

### Evidence & Supporting

| FK Column | Parent Table | Delete Rule |
|-----------|-------------|-------------|
| `evidences.tenant_id` | `app_tenants.id` | — |
| `evidences.owner_user_id` | `local_users.id` | — |
| `evidence_links.tenant_id` | `app_tenants.id` | — |
| `evidence_links.evidence_id` | `evidences.id` | — |
| `audit_logs.tenant_id` | `app_tenants.id` | — |
| `audit_logs.actor_user_id` | `global_users.id` | — |
| `comments.tenant_id` | `app_tenants.id` | — |
| `comments.author_user_id` | `users.id` | — |
| `person_organizations.person_id` | `persons.id` | RESTRICT |
| `person_organizations.tenant_id` | `app_tenants.id` | — |
| `protection_need_summaries.tenant_id` | `app_tenants.id` | CASCADE |
| `protection_need_summaries.business_process_id` | `business_processes.id` | CASCADE |
| `protection_need_summaries.approved_by` | `local_users.id` | SET NULL |
| `protectionmode_selections.tenant_id` | `app_tenants.id` | CASCADE |
| `protectionmode_selections.catalog_version_id` | `eits_catalog_versions.id` | SET NULL |
| `protectionmode_selections.evidence_id` | `evidences.id` | SET NULL |
| `protectionmode_selections.approved_by` | `local_users.id` | SET NULL |
| `security_profiles.tenant_id` | `app_tenants.id` | CASCADE |
| `security_profiles.catalog_version_id` | `eits_catalog_versions.id` | SET NULL |
| `security_profiles.approved_by` | `local_users.id` | SET NULL |
| `damage_assessments.tenant_id` | `app_tenants.id` | CASCADE |
| `damage_assessments.business_process_id` | `business_processes.id` | CASCADE |
| `damage_assessments.damage_scenario_id` | `damage_scenarios.id` | — |
| `damage_assessments.assessed_by` | `local_users.id` | SET NULL |
| `damage_category_thresholds.tenant_id` | `app_tenants.id` | CASCADE |
| `damage_category_thresholds.damage_scenario_id` | `damage_scenarios.id` | CASCADE |
| `damage_category_thresholds.approved_by` | `local_users.id` | SET NULL |

## Check Constraints

| Table | Column | Constraint |
|-------|--------|------------|
| `business_processes` | `process_type` | `IN ('OPERATIVE', 'SUPPORTING')` |
| `business_processes` | `priority` | `BETWEEN 1 AND 3` |
| `assets` | `protection_need` | `IN ('NORMAL', 'HIGH', 'VERY_HIGH')` |
| `eits_catalog_measures` | `measure_level` | `IN ('BASE', 'STANDARD', 'HIGH')` |
| `risks` | `likelihood_score` | `BETWEEN 0 AND 3` |
| `risks` | `impact_score` | `BETWEEN 0 AND 3` |
| `risks` | `treatment_type` | `IN ('MITIGATE', 'ACCEPT', 'TRANSFER', 'AVOID')` |
| `damage_assessments` | `availability_impact` | `BETWEEN 0 AND 3` |
| `damage_assessments` | `confidentiality_impact` | `BETWEEN 0 AND 3` |
| `damage_assessments` | `integrity_impact` | `BETWEEN 0 AND 3` |
| `protection_need_summaries` | `protection_need` | `IN ('NORMAL', 'HIGH', 'VERY_HIGH')` |
| `protection_need_summaries` | `confidentiality_need` | `IN ('NORMAL', 'HIGH', 'VERY_HIGH')` |
| `protection_need_summaries` | `integrity_need` | `IN ('NORMAL', 'HIGH', 'VERY_HIGH')` |
| `protection_need_summaries` | `availability_need` | `IN ('NORMAL', 'HIGH', 'VERY_HIGH')` |
| `security_profiles` | `security_approach` | `IN ('BASIC', 'STANDARD', 'CORE')` |
| `imr_items` | `pearo_status` | `IN ('P', 'E', 'A', 'R', 'O')` |
| `imr_items` | `priority` | `IN ('P1', 'P2', 'P3')` |

## Generated Columns

| Table | Column | Expression | Type |
|-------|--------|------------|------|
| `risks` | `risk_score` | `likelihood_score * impact_score` | GENERATED ALWAYS AS STORED |

## Database Triggers

| Trigger Name | Table | Event | Purpose |
|-------------|-------|-------|---------|
| `check_asset_relation_circular_insert` | `asset_relations` | BEFORE INSERT | Prevents circular dependency chains using recursive CTE |
| `check_asset_relation_circular_update` | `asset_relations` | BEFORE UPDATE OF `target_asset_id` | Prevents circular dependency chains on update |
| `trg_damage_assessment_damage_category` | `damage_assessments` | BEFORE INSERT OR UPDATE | Auto-calculates `damage_category = GREATEST(availability_impact, confidentiality_impact, integrity_impact)` |

## Performance Indexes

The following columns are indexed for query performance (in addition to PKs and FKs which are auto-indexed):

| Table | Indexed Columns |
|-------|-----------------|
| `global_users` | `email` |
| `eits_catalog_versions` | `year`, `is_active` |
| `eits_modules` | `catalog_version_id`, `module_group` |
| `eits_catalog_measures` | `module_id`, `measure_level` |
| `eits_threats` | `version_id` |
| `business_processes` | `tenant_id` |
| `assets` | `tenant_id`, `person_id`, `asset_category` |
| `asset_relation_types` | `code` |
| `asset_relations` | `tenant_id` |
| `process_assets` | `tenant_id` |
| `object_module_mappings` | `tenant_id` |
| `implementation_plan_items` | `tenant_id` |
| `risks` | `tenant_id`, `threat_id`, `asset_id`, `business_process_id` |
| `evidences` | `tenant_id`, `file_hash` |
| `evidence_links` | `tenant_id`, `link_type` |
| `audit_logs` | `tenant_id` |
| `comments` | `tenant_id` |
| `persons` | `national_id` |
| `person_organizations` | `person_id`, `tenant_id` |
| `organization_people` | `tenant_id`, `person_asset_id` |
| `security_profiles` | `tenant_id` |
| `damage_assessments` | `business_process_id` |
| `asset_module_mappings` | `tenant_id`, `asset_id`, `module_id` |
| `bp_module_mappings` | `business_process_id` |
| `imr_items` | `tenant_id`, `bp_module_mapping_id`, `imr_snapshot_id`, `created_by` |
| `imr_snapshots` | `tenant_id`, `protection_mode_selection_id` |
| `risk_measure_links` | `risk_id` |
| `soft-deleted tables` | `deleted_at` |
