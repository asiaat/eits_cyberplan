# Data Dictionary

Flat alphabetical reference of all columns across all database tables.

## Conventions

- `PK` = Primary Key
- `FK` = Foreign Key
- `UQ` = Unique Constraint
- `IX` = Index
- `GEN` = Generated Column
- `CK` = Check Constraint

---

### A

| Column | Table | Type | Constraints | Description |
|--------|-------|------|-------------|-------------|
| `accepted_at` | `risks` | TIMESTAMP WITH TZ | YES | When risk was accepted |
| `accepted_by` | `risks` | UUID | YES | Who accepted the risk |
| `action` | `audit_logs` | VARCHAR(50) | NOT NULL | Action type (create/update/delete) |
| `active` | `eits_catalog_versions` | BOOLEAN | YES `False` | Whether version is active |
| `additional_info` | `persons` | TEXT | YES | Additional information |
| `applicability` | `object_module_mappings` | VARCHAR(50) | YES `'pending'` | Applicability status |
| `approved_at` | `protection_need_summaries` | TIMESTAMP WITH TZ | YES | Approval timestamp |
| `approved_at` | `protectionmode_selections` | TIMESTAMP WITH TZ | YES | When approved |
| `approved_at` | `security_profiles` | TIMESTAMP WITH TZ | YES | When approved |
| `approved_by` | `damage_category_thresholds` | UUID | FK → `local_users.id` | Who approved (SET NULL) |
| `approved_by` | `protection_need_summaries` | UUID | FK → `local_users.id` | Approver (SET NULL) |
| `approved_by` | `protectionmode_selections` | UUID | FK → `local_users.id` | Who approved (SET NULL) |
| `approved_by` | `security_profiles` | UUID | FK → `local_users.id` | Who approved (SET NULL) |
| `asset_category` | `assets` | VARCHAR(5) | IX, FK → `asset_type_categories.code` | Category code (T/V/I/R/A) |
| `asset_id` | `asset_module_mappings` | UUID | FK → `assets.id` (CASCADE), IX | Asset |
| `asset_id` | `process_assets` | UUID | FK → `assets.id` | Asset |
| `asset_id` | `risks` | UUID | IX | Related asset |
| `asset_index` | `assets` | VARCHAR(10) | YES | Asset index number |
| `asset_module_mapping_id` | `imr_items` | UUID | FK → `asset_module_mappings.id` (CASCADE) | Source mapping |
| `asset_type` | `assets` | VARCHAR(50) | NOT NULL | Asset type |
| `assessed_at` | `damage_assessments` | TIMESTAMP WITH TZ | YES `now()` | When assessed |
| `assessed_by` | `damage_assessments` | UUID | FK → `local_users.id` (SET NULL) | Who assessed |
| `assigned_at` | `tenant_users` | TIMESTAMP | YES `now()` | When assigned to tenant |
| `assigned_at` | `process_module_assignments` | TIMESTAMP WITH TZ | YES `now()` | When assigned |
| `assigned_by` | `process_module_assignments` | UUID | FK → `local_users.id` (SET NULL) | Who assigned |
| `auth_provider` | `users` | VARCHAR(50) | YES `'local'` | Auth provider |
| `availability_impact` | `damage_assessments` | INTEGER | YES `0`, CK 0–3 | Availability impact score |
| `availability_need` | `assets` | VARCHAR(20) | YES `'normal'` | Availability protection need |
| `availability_need` | `business_processes` | VARCHAR(20) | YES `'normal'` | Availability protection need |
| `availability_need` | `protection_need_summaries` | VARCHAR(20) | YES `'NORMAL'` | Availability protection need |

### B

| Column | Table | Type | Constraints | Description |
|--------|-------|------|-------------|-------------|
| `before_json` | `audit_logs` | TEXT | YES | State before change |
| `bidirectional` | `asset_relation_types` | BOOLEAN | YES `False` | Bidirectional flag |
| `bidirectional` | `asset_relations` | BOOLEAN | YES `False` | Bidirectional flag |
| `body` | `comments` | TEXT | NOT NULL | Comment content |
| `bp_module_mapping_id` | `imr_items` | UUID | FK → `bp_module_mappings.id` (CASCADE), IX | Source mapping |
| `business_process_id` | `bp_module_mappings` | UUID | FK → `business_processes.id` (CASCADE), IX | Business process |
| `business_process_id` | `damage_assessments` | UUID | FK → `business_processes.id` (CASCADE), IX | Business process |
| `business_process_id` | `damage_category_thresholds` | — | — | (In damage_category_thresholds via scenario) |
| `business_process_id` | `process_assets` | UUID | FK → `business_processes.id` | Business process |
| `business_process_id` | `protection_need_summaries` | UUID | FK → `business_processes.id` (CASCADE) | Business process |
| `business_process_id` | `risks` | UUID | IX | Related business process |

### C

| Column | Table | Type | Constraints | Description |
|--------|-------|------|-------------|-------------|
| `catalog_version_id` | `eits_catalog_measures` | — | — | Via module |
| `catalog_version_id` | `eits_measures` | UUID | FK → `eits_catalog_versions.id` | Catalog version |
| `catalog_version_id` | `eits_modules` | UUID | FK → `eits_catalog_versions.id`, IX | Catalog version |
| `catalog_version_id` | `protectionmode_selections` | UUID | FK → `eits_catalog_versions.id` (SET NULL) | Catalog version |
| `catalog_version_id` | `security_profiles` | UUID | FK → `eits_catalog_versions.id` (SET NULL) | Catalog version |
| `category` | `eits_modules` | VARCHAR(100) | YES | Module category |
| `category` | `eits_threats` | VARCHAR(100) | YES | Threat category |
| `category` | `permissions` | VARCHAR(50) | YES | Permission category |
| `code` | `asset_relation_types` | VARCHAR(50) | NOT NULL, UQ, IX | Relation type code |
| `code` | `asset_type_categories` | VARCHAR(5) | NOT NULL, UQ | Category code |
| `code` | `damage_scenarios` | VARCHAR(10) | NOT NULL, UQ | Scenario code |
| `code` | `eits_catalog_measures` | VARCHAR(30) | NOT NULL | Measure code |
| `code` | `eits_measures` | VARCHAR(50) | NOT NULL | Measure code |
| `code` | `eits_modules` | VARCHAR(50) | NOT NULL | Module code |
| `code` | `eits_threats` | VARCHAR(30) | NOT NULL | Threat code |
| `code` | `permissions` | VARCHAR(100) | NOT NULL, UQ | Permission code |
| `code` | `roles` | VARCHAR(50) | NOT NULL, UQ | Role code |
| `company_type` | `tenants` | VARCHAR(20) | YES | Company type |
| `confidentiality_impact` | `damage_assessments` | INTEGER | YES `0`, CK 0–3 | Confidentiality impact score |
| `confidentiality_need` | `assets` | VARCHAR(20) | YES `'normal'` | Confidentiality protection need |
| `confidentiality_need` | `business_processes` | VARCHAR(20) | YES `'normal'` | Confidentiality protection need |
| `confidentiality_need` | `protection_need_summaries` | VARCHAR(20) | YES `'NORMAL'` | Confidentiality protection need |
| `contact_address` | `tenants` | TEXT | YES | Contact address |
| `cost_eur` | `imr_items` | NUMERIC(12,2) | YES | Estimated cost in EUR |
| `created_at` | (most tables) | TIMESTAMP | YES `now()` | Creation timestamp |
| `created_by` | `imr_items` | UUID | FK → `local_users.id` (SET NULL), IX | Who created this item |
| `created_by` | `imr_snapshots` | UUID | FK → `local_users.id` (SET NULL) | Who created |
| `criticality` | `assets` | VARCHAR(20) | YES `'normal'` | Asset criticality |
| `custom_measure_description` | `risk_measure_links` | TEXT | YES | Custom measure description |
| `custom_measure_name` | `risk_measure_links` | VARCHAR(255) | YES | Custom measure name |

### D

| Column | Table | Type | Constraints | Description |
|--------|-------|------|-------------|-------------|
| `damage_category` | `damage_assessments` | INTEGER | YES, CALC | Auto-calculated GREATEST of impacts |
| `damage_scenario_id` | `damage_assessments` | UUID | FK → `damage_scenarios.id` | Damage scenario |
| `damage_scenario_id` | `damage_category_thresholds` | UUID | FK → `damage_scenarios.id` (CASCADE) | Damage scenario |
| `date_of_birth` | `persons` | DATE | YES | Date of birth |
| `deleted_at` | (soft-delete tables) | TIMESTAMP | YES | Soft delete timestamp, IX |
| `deleted_by` | (soft-delete tables) | UUID | YES | Who deleted |
| `department` | `local_users` | VARCHAR(100) | YES | Department |
| `dependency_type` | `business_process_dependencies` | VARCHAR(50) | YES | Type of dependency |
| `depends_on_process_id` | `business_process_dependencies` | UUID | FK → `business_processes.id` (CASCADE) | Process being depended on |
| `description` | `asset_relation_types` | TEXT | YES | Description |
| `description` | `asset_relations` | TEXT | YES | Description |
| `description` | `business_process_dependencies` | TEXT | YES | Description of dependency |
| `description` | `business_processes` | TEXT | YES | Process description |
| `description` | `damage_scenarios` | TEXT | YES | Scenario description |
| `description` | `damage_category_thresholds` | — | — | (4 levels per scenario) |
| `description` | `eits_catalog_measures` | TEXT | YES | Measure description |
| `description` | `eits_measures` | TEXT | YES | Measure description |
| `description` | `eits_modules` | TEXT | YES | Module description |
| `description` | `eits_threats` | TEXT | YES | Threat description |
| `description` | `imr_snapshots` | TEXT | YES | Snapshot description |
| `description` | `roles` | TEXT | YES | Role description |
| `description` | `e_its_roles` | TEXT | YES | Role description |
| `divisions` | `app_tenants` | VARCHAR(5000) | YES | JSON array of divisions |
| `divisions` | `tenants` | JSON | YES `[]` | Organizational divisions |
| `division_id` | `business_processes` | UUID | YES | Organizational division |
| `download_count` | `evidences` | INTEGER | YES `0` | Download count |
| `due_date` | `imr_items` | DATE | YES | Target completion date |
| `due_date` | `implementation_plan_items` | TIMESTAMP | YES | Due date |

### E–G

| Column | Table | Type | Constraints | Description |
|--------|-------|------|-------------|-------------|
| `email` | `app_tenants` | VARCHAR(255) | YES | Contact email |
| `email` | `global_users` | VARCHAR(255) | NOT NULL, UQ, IX | Email |
| `email` | `persons` | VARCHAR(255) | YES | Email |
| `email` | `tenants` | VARCHAR(255) | YES | Email |
| `email` | `users` | VARCHAR(255) | NOT NULL, UQ, IX | Email |
| `entity_id` | `audit_logs` | UUID | NOT NULL | ID of affected entity |
| `entity_type` | `audit_logs` | VARCHAR(50) | NOT NULL | Type of affected entity |
| `entity_type` | `comments` | VARCHAR(50) | NOT NULL | Entity type |
| `entity_id` | `comments` | UUID | NOT NULL | Entity ID |
| `evidence_id` | `evidence_links` | UUID | FK → `evidences.id` | Evidence |
| `evidence_id` | `protectionmode_selections` | UUID | FK → `evidences.id` (SET NULL) | Supporting evidence |
| `evidence_type` | `evidences` | VARCHAR(50) | NOT NULL | Type (file/url/text) |
| `external_url` | `evidences` | VARCHAR(500) | YES | External URL |
| `file_hash` | `evidences` | VARCHAR(64) | YES, IX | SHA-256 hash |
| `file_size` | `evidences` | BIGINT | YES | File size in bytes |
| `first_name` | `persons` | VARCHAR(100) | NOT NULL | First name |
| `full_name` | `local_users` | VARCHAR(255) | NOT NULL | Display name |
| `global_user_id` | `local_users` | UUID | FK → `global_users.id` (CASCADE) | Global identity |
| `granted_at` | `user_roles` | TIMESTAMP | YES `now()` | When granted |
| `granted_by` | `user_roles` | UUID | FK → `local_users.id` | Who granted |
| `group_name` | `assets` | VARCHAR(255) | YES | Group name for grouped assets |

### H–L

| Column | Table | Type | Constraints | Description |
|--------|-------|------|-------------|-------------|
| `hashed_password` | `users` | VARCHAR(255) | YES | Password hash |
| `id` | (all tables) | UUID/PK | PK, `uuid4` | Primary key |
| `impact` | `risks` | VARCHAR(20) | YES | Legacy impact value |
| `impact_area` | `eits_threats` | VARCHAR(100) | YES | Impact area |
| `impact_score` | `risks` | INTEGER | YES, CK 0–3 | Impact score |
| `implementation_comment` | `implementation_plan_items` | TEXT | YES | Implementation notes |
| `implementation_description` | `imr_items` | TEXT | YES | Implementation description |
| `implementation_guidance` | `eits_measures` | TEXT | YES | Implementation guidance |
| `imported_at` | `eits_catalog_versions` | TIMESTAMP | YES `now()` | Import timestamp |
| `inputs` | `business_processes` | TEXT | YES | Process inputs |
| `integrity_impact` | `damage_assessments` | INTEGER | YES `0`, CK 0–3 | Integrity impact score |
| `integrity_need` | `assets` | VARCHAR(20) | YES `'normal'` | Integrity protection need |
| `integrity_need` | `business_processes` | VARCHAR(20) | YES `'normal'` | Integrity protection need |
| `integrity_need` | `protection_need_summaries` | VARCHAR(20) | YES `'NORMAL'` | Integrity protection need |
| `is_active` | `eits_catalog_versions` | BOOLEAN | YES `False`, IX | Active flag |
| `is_active` | `local_users` | BOOLEAN | YES `True` | Active status |
| `is_active` | `protectionmode_selections` | BOOLEAN | NOT NULL `True` | Active flag |
| `is_active` | `alerts` | VARCHAR(10) | NOT NULL `"true"` | Active flag |
| `is_active` | `users` | BOOLEAN | YES `True` | Active status |
| `is_applicable` | `process_module_assignments` | VARCHAR(1) | YES `'1'` | Applicable flag |
| `is_core` | `assets` | BOOLEAN | NOT NULL `false` | Core asset flag |
| `is_current` | `imr_snapshots` | BOOLEAN | NOT NULL `False` | Current snapshot flag |
| `is_default` | `roles` | VARCHAR(10) | YES `'false'` | Default role flag |
| `is_grouped` | `assets` | BOOLEAN | NOT NULL `false` | Grouped asset flag |
| `is_process_module_measure` | `imr_items` | BOOLEAN | YES `False` | From process module |
| `is_read` | `alerts` | VARCHAR(10) | NOT NULL `"false"` | Read flag |
| `item_count` | `imr_snapshots` | INTEGER | NOT NULL `0` | IMR item count |
| `justification` | `asset_module_mappings` | TEXT | YES | Why module selected |
| `justification` | `bp_module_mappings` | TEXT | YES | Why module selected |
| `justification` | `damage_assessments` | TEXT | YES | Assessment justification |
| `justification` | `protection_need_summaries` | TEXT | YES | Rationale |
| `label` | `imr_snapshots` | VARCHAR(255) | NOT NULL | Snapshot label |
| `last_name` | `persons` | VARCHAR(100) | NOT NULL | Last name |
| `last_verified_at` | `imr_items` | TIMESTAMP WITH TZ | YES | Last verification |
| `legal_form` | `app_tenants` | VARCHAR(255) | YES | Legal form |
| `legal_form` | `tenants` | VARCHAR(50) | YES | Legal form |
| `level` | `alerts` | ENUM | NOT NULL `'info'` | Alert level |
| `lifecycle_status` | `assets` | VARCHAR(50) | YES `'active'` | Lifecycle status |
| `likelihood` | `risks` | VARCHAR(20) | YES | Legacy likelihood |
| `likelihood_score` | `risks` | INTEGER | YES, CK 0–3 | Likelihood score |
| `link` | `alerts` | VARCHAR(255) | YES | Deep link URL |
| `link_type` | `evidence_links` | VARCHAR(50) | YES `'general'`, IX | Type of link |
| `location` | `assets` | VARCHAR(255) | YES | Physical/virtual location |

### M–N

| Column | Table | Type | Constraints | Description |
|--------|-------|------|-------------|-------------|
| `measure_id` | `eits_catalog_measures` | — | — | (self) |
| `measure_id` | `eits_module_measures` | UUID | FK → `eits_measures.id` | Measure |
| `measure_id` | `implementation_plan_items` | UUID | FK → `eits_measures.id` | Measure |
| `measure_id` | `imr_items` | UUID | FK → `eits_catalog_measures.id` (CASCADE) | Catalog measure |
| `measure_id` | `risk_measure_links` | UUID | FK → `eits_catalog_measures.id` (SET NULL) | Catalog measure |
| `measure_level` | `eits_catalog_measures` | VARCHAR(10) | NOT NULL, CK IN ('BASE','STANDARD','HIGH'), IX | Measure level |
| `measure_level` | `eits_measures` | VARCHAR(50) | YES | Measure level |
| `message` | `alerts` | TEXT | YES | Alert message |
| `mfa_enabled` | `global_users` | BOOLEAN | YES `False` | MFA enabled |
| `mfa_secret` | `global_users` | VARCHAR(255) | YES | MFA TOTP secret |
| `mime_type` | `evidences` | VARCHAR(100) | YES | MIME type |
| `modeled_at` | `asset_module_mappings` | TIMESTAMP WITH TZ | YES `now()` | When modeled |
| `modeled_at` | `bp_module_mappings` | TIMESTAMP WITH TZ | YES `now()` | When modeled |
| `modeled_by` | `asset_module_mappings` | UUID | FK → `local_users.id` (SET NULL) | Who modeled |
| `modeled_by` | `bp_module_mappings` | UUID | FK → `local_users.id` (SET NULL) | Who modeled |
| `module_group` | `eits_modules` | VARCHAR(10) | YES, IX | Module group |
| `module_id` | `asset_module_mappings` | UUID | FK → `eits_modules.id` (CASCADE) | Module |
| `module_id` | `bp_module_mappings` | UUID | FK → `eits_modules.id` (CASCADE) | Module |
| `module_id` | `eits_catalog_measures` | UUID | FK → `eits_modules.id` (CASCADE), IX | Module |
| `module_id` | `eits_module_measures` | UUID | FK → `eits_modules.id` | Module |
| `module_id` | `module_threats` | UUID | FK → `eits_modules.id` (CASCADE) | Module |
| `module_id` | `object_module_mappings` | UUID | FK → `eits_modules.id` | Module |
| `module_id` | `process_module_assignments` | UUID | FK → `eits_modules.id` (CASCADE) | Module |
| `module_type` | `eits_modules` | VARCHAR(50) | YES | Module type |
| `nace_codes` | `tenants` | JSON | YES | NACE codes |
| `name` | `app_tenants` | VARCHAR(255) | NOT NULL | Organization name |
| `name` | `asset_relation_types` | VARCHAR(255) | NOT NULL | Display name |
| `name` | `asset_type_categories` | VARCHAR(100) | NOT NULL | Category name |
| `name` | `damage_scenarios` | VARCHAR(255) | NOT NULL | Scenario name |
| `name` | `eits_catalog_measures` | VARCHAR(255) | NOT NULL | Measure name |
| `name` | `eits_modules` | VARCHAR(255) | NOT NULL | Module name |
| `name` | `eits_threats` | VARCHAR(255) | NOT NULL | Threat name |
| `name` | `eits_catalog_versions` | VARCHAR(100) | YES | Version name |
| `name` | `permissions` | VARCHAR(100) | NOT NULL | Display name |
| `name` | `roles` | VARCHAR(100) | NOT NULL | Role name |
| `name` | `tenants` | VARCHAR(255) | NOT NULL | Organization name |
| `name` | `users` | VARCHAR(255) | NOT NULL | User name |
| `national_id` | `persons` | VARCHAR(50) | YES, UQ | National ID |
| `next_review_date` | `imr_items` | DATE | YES | Next review date |
| `non_applicability_justification` | `process_module_assignments` | TEXT | YES | Why not applicable |
| `non_implementation_justification` | `imr_items` | TEXT | YES | Reason not implemented |
| `notes` | `protectionmode_selections` | TEXT | YES | Additional notes |
| `notes` | `security_profiles` | TEXT | YES | Additional notes |

### O–Q

| Column | Table | Type | Constraints | Description |
|--------|-------|------|-------------|-------------|
| `outputs` | `business_processes` | TEXT | YES | Process outputs |
| `owner_user_id` | `assets` | UUID | FK → `users.id` | Asset owner (legacy) |
| `owner_user_id` | `business_processes` | UUID | FK → `local_users.id` | Process owner |
| `owner_user_id` | `evidences` | UUID | FK → `local_users.id` | Evidence owner |
| `owner_user_id` | `implementation_plan_items` | UUID | FK → `users.id` | Owner (legacy) |
| `owner_user_id` | `risks` | UUID | FK → `users.id` | Risk owner (legacy) |
| `parent_company_id` | `tenants` | UUID | FK → `tenants.id` | Parent company |
| `partial_scope_description` | `imr_items` | TEXT | YES | Partial implementation scope |
| `password_hash` | `global_users` | VARCHAR(255) | NOT NULL | Password hash |
| `pearo_status` | `imr_items` | VARCHAR(1) | NOT NULL `'E'`, CK IN ('P','E','A','R','O') | PEARO implementation status |
| `permission_id` | `e_its_role_permissions` | TEXT | PK, FK → `permissions.id` (CASCADE) | Permission |
| `permission_id` | `role_permissions` | TEXT | PK, FK → `permissions.id` (CASCADE) | Permission |
| `person_asset_id` | `organization_people` | UUID | NOT NULL, IX | Person/asset ID |
| `person_id` | `assets` | UUID | FK → `persons.id` (RESTRICT), IX | Responsible person |
| `person_id` | `person_organizations` | UUID | FK → `persons.id` (RESTRICT), IX | Person |
| `phone` | `app_tenants` | VARCHAR(50) | YES | Contact phone |
| `phone` | `persons` | VARCHAR(50) | YES | Phone |
| `phone` | `tenants` | VARCHAR(50) | YES | Phone |
| `plan` | `app_tenants` | VARCHAR(50) | YES | Subscription plan |
| `primary_process_id` | `business_process_dependencies` | UUID | FK → `business_processes.id` (CASCADE) | Process that depends |
| `priority` | `business_processes` | INTEGER | YES `2`, CK 1–3 | Process priority |
| `priority` | `imr_items` | VARCHAR(5) | YES `'P2'`, CK IN ('P1','P2','P3') | IMR priority |
| `priority` | `implementation_plan_items` | VARCHAR(20) | YES `'medium'` | Priority |
| `process_type` | `business_processes` | VARCHAR(20) | YES `'OPERATIVE'`, CK IN ('OPERATIVE','SUPPORTING') | Process type |
| `protection_need` | `assets` | VARCHAR(20) | YES `'NORMAL'`, CK IN ('NORMAL','HIGH','VERY_HIGH') | Overall protection need |
| `protection_need` | `protection_need_summaries` | VARCHAR(20) | NOT NULL `'NORMAL'`, CK IN ('NORMAL','HIGH','VERY_HIGH') | Protection need |
| `protection_need_justification` | `assets` | TEXT | YES | Justification |
| `protection_source_process_ids` | `assets` | ARRAY(UUID) | YES | Source BP IDs |
| `protection_mode_selection_id` | `imr_snapshots` | UUID | FK → `protectionmode_selections.id` (SET NULL), IX | Protection mode |
| `purpose` | `business_processes` | TEXT | YES | Process purpose |

### R

| Column | Table | Type | Constraints | Description |
|--------|-------|------|-------------|-------------|
| `rationale` | `object_module_mappings` | TEXT | YES | Mapping rationale |
| `read_at` | `alerts` | TIMESTAMP | YES | Read timestamp |
| `registered_address` | `app_tenants` | VARCHAR(500) | YES | Registered address |
| `registered_address` | `tenants` | TEXT | YES | Registered address |
| `registration_date` | `tenants` | DATE | YES | Registration date |
| `registry_code` | `app_tenants` | VARCHAR(50) | YES | Organization registry code |
| `registry_code` | `tenants` | VARCHAR(20) | YES, UQ | Registry code |
| `relation_description` | `process_assets` | TEXT | YES | How asset relates to process |
| `relation_type` | `asset_relations` | VARCHAR(50) | NOT NULL | Legacy relation type |
| `relation_type_code` | `asset_relations` | VARCHAR(50) | FK → `asset_relation_types.code` | Relation type code |
| `released_at` | `eits_catalog_versions` | DATE | YES | Release date |
| `relevance_note` | `module_threats` | TEXT | YES | Relevance note |
| `remarks` | `assets` | TEXT | YES | Additional remarks |
| `requirement_profile` | `imr_items` | VARCHAR(20) | YES | Requirement profile |
| `residual_risk_level` | `risks` | VARCHAR(20) | YES | Residual risk |
| `responsible_role` | `eits_catalog_measures` | VARCHAR(100) | YES | Responsible role |
| `responsible_role` | `eits_measures` | VARCHAR(100) | YES | Responsible role |
| `responsible_user_id` | `imr_items` | UUID | FK → `local_users.id` (SET NULL) | Responsible person |
| `restored_from` | `imr_snapshots` | UUID | YES | Restored from snapshot |
| `review_date` | `risks` | TIMESTAMP | YES | Review date |
| `review_due_date` | `evidences` | TIMESTAMP | YES | Review deadline |
| `risk_acceptance_approved_by` | `imr_items` | UUID | FK → `local_users.id` (SET NULL) | Risk acceptance approver |
| `risk_acceptance_date` | `imr_items` | TIMESTAMP WITH TZ | YES | Acceptance date |
| `risk_id` | `risk_measure_links` | UUID | FK → `risks.id` (CASCADE), IX | Risk |
| `risk_level` | `risks` | VARCHAR(20) | YES | Calculated risk level |
| `risk_rating` | `risks` | VARCHAR(20) | YES | Risk rating label |
| `risk_score` | `risks` | INTEGER | GEN | `likelihood * impact` (STORED) |
| `role` | `person_organizations` | VARCHAR(100) | YES | Role within organization |
| `role_id` | `e_its_role_permissions` | UUID | PK, FK → `e_its_roles.id` (CASCADE) | E-ITS role |
| `role_id` | `memberships` | VARCHAR(50) | FK → `roles.id` | Legacy role |
| `role_id` | `role_permissions` | TEXT | PK, FK → `roles.id` (CASCADE) | Legacy role |
| `role_id` | `user_roles` | UUID | FK → `e_its_roles.id` (CASCADE) | E-ITS role |
| `role_name` | `e_its_roles` | VARCHAR(100) | NOT NULL | Role name |

### S

| Column | Table | Type | Constraints | Description |
|--------|-------|------|-------------|-------------|
| `scenario` | `risks` | TEXT | YES | Risk scenario |
| `security_approach` | `protectionmode_selections` | VARCHAR(20) | NOT NULL `'BASIC'` | Approach |
| `security_approach` | `security_profiles` | VARCHAR(20) | NOT NULL `'BASIC'`, CK IN ('BASIC','STANDARD','CORE') | Approach |
| `selected_at` | `object_module_mappings` | TIMESTAMP | YES `now()` | When selected |
| `selected_by_user_id` | `object_module_mappings` | UUID | FK → `users.id` | User who mapped |
| `share_capital` | `tenants` | NUMERIC(15,2) | YES | Share capital |
| `source_asset_id` | `asset_relations` | UUID | FK → `assets.id` | Source asset |
| `source_file_hash` | `eits_catalog_versions` | VARCHAR(64) | YES | Source file hash |
| `source_name` | `eits_catalog_versions` | VARCHAR(255) | YES | Source file name |
| `source_types` | `asset_relation_types` | VARCHAR(500) | YES | Valid source asset types (JSON) |
| `source_url` | `eits_modules` | VARCHAR(500) | YES | Reference URL |
| `status` | `app_tenants` | VARCHAR(50) | YES `'active'` | Tenant status |
| `status` | `business_processes` | VARCHAR(50) | YES `'active'` | Process status |
| `status` | `implementation_plan_items` | VARCHAR(50) | YES `'not_started'` | Status |
| `status` | `risks` | VARCHAR(50) | YES `'identified'` | Risk status |
| `status` | `tenants` | VARCHAR(50) | YES | Tenant status |
| `status_changed_at` | `imr_items` | TIMESTAMP WITH TZ | YES | Last status change |
| `storage_uri` | `evidences` | VARCHAR(500) | YES | S3/MinIO URI |
| `strength` | `asset_relation_types` | VARCHAR(20) | YES `'weak'` | Default strength |
| `strength` | `asset_relations` | VARCHAR(20) | YES `'weak'` | Relationship strength |

### T–Z

| Column | Table | Type | Constraints | Description |
|--------|-------|------|-------------|-------------|
| `target_asset_id` | `asset_relations` | UUID | FK → `assets.id` | Target asset |
| `target_id` | `evidence_links` | UUID | NOT NULL | ID of linked entity |
| `target_id` | `implementation_plan_items` | UUID | NOT NULL | Target ID |
| `target_id` | `object_module_mappings` | UUID | NOT NULL | Target object ID |
| `target_id` | `risks` | UUID | YES | Target object ID |
| `target_role` | `alerts` | ENUM | NOT NULL `'all'` | Target role |
| `target_type` | `evidence_links` | VARCHAR(50) | NOT NULL | Linked entity type |
| `target_type` | `implementation_plan_items` | VARCHAR(50) | NOT NULL | Target type |
| `target_type` | `object_module_mappings` | VARCHAR(50) | NOT NULL | Target object type |
| `target_type` | `risks` | VARCHAR(50) | YES | Target type |
| `target_types` | `asset_relation_types` | VARCHAR(500) | YES | Valid target asset types (JSON) |
| `tenant_id` | (tenant-scoped tables) | UUID | FK → `app_tenants.id`, IX | Tenant |
| `tenant_id` | `alerts` | UUID | YES | Tenant (nullable) |
| `tenant_id` | `person_organizations` | UUID | FK → `app_tenants.id`, IX | Tenant |
| `threat` | `risks` | TEXT | YES | Threat description |
| `threat_id` | `module_threats` | UUID | FK → `eits_threats.id` (CASCADE) | Threat |
| `threat_id` | `risks` | UUID | IX | Threat (FK to eits_threats) |
| `title` | `eits_measures` | VARCHAR(255) | NOT NULL | Measure title |
| `title` | `evidences` | VARCHAR(255) | NOT NULL | Evidence title |
| `title` | `risks` | VARCHAR(255) | NOT NULL | Risk title |
| `title` | `alerts` | VARCHAR(255) | NOT NULL | Alert title |
| `todo_description` | `imr_items` | TEXT | YES | Action description |
| `treatment` | `risks` | VARCHAR(50) | YES | Legacy treatment |
| `treatment_type` | `risks` | VARCHAR(30) | YES, CK IN ('MITIGATE','ACCEPT','TRANSFER','AVOID') | Treatment type |
| `updated_at` | (various) | TIMESTAMP | YES `now()` | Last update |
| `updated_by` | `imr_items` | UUID | FK → `local_users.id` (SET NULL) | Who updated |
| `user_id` | `memberships` | UUID | FK → `users.id` | User (legacy) |
| `user_id` | `tenant_users` | UUID | PK, FK → `global_users.id` (CASCADE) | Global user |
| `user_id` | `user_roles` | UUID | FK → `local_users.id` (CASCADE) | Local user |
| `valid_from` | `evidences` | TIMESTAMP | YES | Validity start |
| `valid_until` | `evidences` | TIMESTAMP | YES | Validity end |
| `verification_method` | `imr_items` | TEXT | YES | Verification method |
| `verification_method` | `implementation_plan_items` | TEXT | YES | Verification method |
| `version` | `eits_catalog_versions` | VARCHAR(50) | NOT NULL | Version string |
| `version` | `evidences` | VARCHAR(20) | YES | Evidence version |
| `version_id` | `eits_threats` | UUID | FK → `eits_catalog_versions.id` (CASCADE), IX | Catalog version |
| `vulnerability` | `risks` | TEXT | YES | Vulnerability description |
| `website` | `tenants` | VARCHAR(255) | YES | Website URL |
| `year` | `eits_catalog_versions` | VARCHAR(4) | YES, IX | Release year |
