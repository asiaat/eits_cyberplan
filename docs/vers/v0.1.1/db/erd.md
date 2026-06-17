# Entity-Relationship Diagram (Textual)

## Tier A — Subscription Layer

```
  ┌──────────────────────┐          ┌──────────────────────┐
  │     app_tenants      │          │     global_users     │
  ├──────────────────────┤          ├──────────────────────┤
  │ id (PK)              │1        N│ id (PK)              │
  │ name                 │◄─────────│ email (UQ, INDEX)    │
  │ status               │          │ password_hash         │
  │ plan                 │          │ mfa_enabled           │
  │ registry_code        │          │ mfa_secret            │
  │ legal_form           │          │ created_at            │
  │ registered_address   │          └──────────┬───────────┘
  │ phone                │                     │N
  │ email                │                     │
  │ divisions            │                     │
  │ created_at           │                     │
  └──────────┬───────────┘                     │
             │1                               │
             │                                │
             │        ┌───────────────────┐    │
             │        │   tenant_users    │    │
             │        ├───────────────────┤    │
             └────────┤ tenant_id (PK,FK) │────┘
                      │ user_id (PK,FK)   │
                      │ assigned_at       │
                      └───────────────────┘
```

## Tier B — Per-Tenant IAM

```
  ┌──────────────┐          ┌────────────────┐          ┌──────────────┐
  │ app_tenants  │          │  local_users   │          │  e_its_roles │
  ├──────────────┤          ├────────────────┤          ├──────────────┤
  │ id (PK)      │1        N│ id (PK)        │          │ id (PK)      │
  └──────┬───────┘     ┌───│ tenant_id (FK)  │          │ tenant_id(FK)│
         │             │   │ global_user_id  │          │ role_name    │
         │1            │   │ full_name       │          │ description  │
         │             │   │ department      │          └──────┬───────┘
         │             │   │ is_active       │                 │1
         │             │   └────────┬────────┘                 │
         │             │            │1                         │
         │             │            │                          │
         │             │            │N                         │N
         │             │   ┌────────┴────────┐   ┌─────────────┴──────────────┐
         │             │   │   user_roles    │   │  e_its_role_permissions    │
         │             │   ├─────────────────┤   ├────────────────────────────┤
         │             │   │ id (PK)         │   │ role_id (PK,FK)            │
         │             └───│ user_id (FK)    │   │ permission_id (PK,FK)      │
         │                 │ role_id (FK)    │   └────────────┬───────────────┘
         │                 │ granted_by (FK) │                │N
         │                 │ granted_at      │                │
         │                 └─────────────────┘                │
         │                                                    │1
         │                                            ┌───────┴──────────┐
         │                                            │   permissions    │
         │                                            ├──────────────────┤
         │                                            │ id (PK)          │
         │                                            │ code (UQ)        │
         │                                            │ name             │
         │                                            │ description      │
         │                                            │ category         │
         │                                            └──────────────────┘
```

## Core Business — Business Processes & Assets

```
  ┌──────────────────┐          ┌──────────────────────┐
  │  app_tenants     │          │ business_processes   │
  ├──────────────────┤          ├──────────────────────┤
  │ id (PK)          │1        N│ id (PK)              │
  └────────┬─────────┘          │ tenant_id (FK)       │
           │                    │ owner_user_id (FK)   │
           │1                   │ division_id           │
           │                    │ name                  │
           │                    │ description           │
           │                    │ purpose               │
           │                    │ inputs                │
           │                    │ outputs               │
           │                    │ status                │
           │                    │ confidentiality_need  │
           │                    │ integrity_need        │
           │                    │ availability_need     │
           │                    │ process_type          │
           │                    │ priority              │
           │                    │ created_at            │
           │                    │ updated_at            │
           │                    │ deleted_at            │ (soft-delete)
           │                    │ deleted_by            │
           │                    └──────────┬────────────┘
           │                               │1
           │                               │
           │                    ┌──────────┴────────────┐
           │                    │bp_dependencies        │
           │                    ├───────────────────────┤
           │                    │ id (PK)               │
           │                    │ tenant_id (FK)        │
           │                    │ primary_process_id(FK)│
           │                    │ depends_on_process_id │
           │                    │ dependency_type       │
           │                    │ description           │
           │                    │ created_at            │
           │                    │ UQ(primary, depends_on)│
           │                    └───────────────────────┘
           │
           │1      ┌───────────────────────┐
           │       │      assets           │
           │       ├───────────────────────┤
           └───────│ tenant_id (FK)        │
                   │ id (PK)               │
                   │ owner_user_id (FK)    │
                   │ person_id (FK)        │
                   │ name                  │
                   │ asset_type            │
                   │ description           │
                   │ criticality           │
                   │ confidentiality_need  │
                   │ integrity_need        │
                   │ availability_need     │
                   │ lifecycle_status      │
                   │ asset_index           │
                   │ asset_category (FK)   │
                   │ is_grouped            │
                   │ quantity              │
                   │ group_name            │
                   │ is_core               │
                   │ location              │
                   │ protection_need       │
                   │ protection_need_just  │
                   │ protection_source_ids │ (ARRAY)
                   │ deleted_at            │
                   └───────────┬───────────┘
                               │1
                    ┌──────────┴───────────┐
                    │  process_assets      │
                    ├──────────────────────┤
                    │ id (PK)              │
                    │ tenant_id (FK)       │
                    │ business_process_id  │
                    │ asset_id (FK)        │
                    │ relation_description │
                    └──────────────────────┘

  ┌─────────────────────┐     ┌──────────────────────┐
  │   asset_relations   │     │  asset_relation_types│
  ├─────────────────────┤     ├──────────────────────┤
  │ id (PK)             │     │ id (PK)              │
  │ tenant_id (FK)      │     │ code (UQ, INDEX)     │
  │ source_asset_id(FK) │N:1  │ name                 │
  │ target_asset_id(FK) │────▶│ description          │
  │ relation_type       │     │ source_types         │
  │ relation_type_code  │     │ target_types         │
  │ description         │     │ bidirectional        │
  │ bidirectional       │     │ strength             │
  │ strength            │     └──────────────────────┘
  │ created_at          │
  │ (circular-check trg) │
  └─────────────────────┘
```

## E-ITS Catalog

```
  ┌──────────────────────┐
  │ eits_catalog_versions│
  ├──────────────────────┤
  │ id (PK)              │
  │ version              │
  │ year (INDEX)         │
  │ name                 │
  │ source_name          │
  │ source_file_hash     │
  │ imported_at          │
  │ active               │
  │ is_active (INDEX)    │
  │ released_at          │
  └──────┬───────────────┘
         │1
    ┌────┴──────────────────┬───────────────────┬──────────────────┐
    │                       │                   │                  │
    │1                      │1                  │1                 │1
  ┌─┴──────────────┐  ┌────┴─────────┐  ┌──────┴──────┐  ┌───────┴──────────┐
  │  eits_modules  │  │ eits_measures│  │eits_catalog │  │   eits_threats   │
  ├────────────────┤  ├──────────────┤  │  _measures  │  ├──────────────────┤
  │ id (PK)        │  │ id (PK)      │  ├─────────────┤  │ id (PK)          │
  │ catalog_ver(FK)│  │ catalog_v(FK)│  │ id (PK)     │  │ version_id (FK)  │
  │ code           │  │ code         │  │ module_id   │  │ code             │
  │ name           │  │ title        │  │ code        │  │ category         │
  │ module_group   │  │ description  │  │ name        │  │ impact_area      │
  │ category       │  │ measure_level│  │ measure_lvl │  │ name             │
  │ description    │  │ responsible  │  │ description │  │ description      │
  │ module_type    │  │ impl_guidance│  │ responsible │  │ UQ(version,code) │
  │ source_url     │  └──────────────┘  └──────┬──────┘  └────────┬─────────┘
  └───────┬───────┘                            │                  │
          │1                                   │1                 │1
          │     ┌─────────────────────┐        │                  │
          │     │ eits_module_measures│        │                  │
          │     ├─────────────────────┤        │                  │
          └─────│ module_id (FK)      │◄───────┘                  │
                │ measure_id (FK)     │                           │
                └─────────────────────┘                           │
          │                                                       │
          │     ┌─────────────────────┐                           │
          │     │   module_threats    │                           │
          │     ├─────────────────────┤                           │
          └─────│ module_id (FK)      │                           │
                │ threat_id (FK)      │◄──────────────────────────┘
                │ relevance_note      │
                └─────────────────────┘

  ┌──────────────────────┐
  │   damage_scenarios   │
  ├──────────────────────┤
  │ id (PK)              │
  │ code (UQ)            │  (KS1-KS6)
  │ name                 │
  │ description          │
  └──────────────────────┘
```

## Module Mappings

```
  ┌──────────────┐     ┌───────────────────────┐     ┌──────────────┐
  │   assets     │     │ asset_module_mappings │     │ eits_modules │
  ├──────────────┤     ├───────────────────────┤     ├──────────────┤
  │ id (PK)      │1   N│ id (PK)               │N   1│ id (PK)      │
  └──────┬───────┘─────│ asset_id (FK)         │─────└──────────────┘
         │             │ module_id (FK)         │
         │             │ justification          │
         │             │ modeled_by (FK)        │
         │             │ modeled_at             │
         │             │ UQ(tenant,asset,module)│
         │             └───────────────────────┘
         │
         │             ┌───────────────────────┐
         │             │ bp_module_mappings    │
         │             ├───────────────────────┤
         └─────────────│ bp_id (FK)            │
                       │ module_id (FK)        │
                       │ justification         │
                       │ modeled_by (FK)       │
                       │ modeled_at            │
                       │ UQ(tenant,bp,module)  │
                       └───────────────────────┘

  ┌───────────────────────┐     ┌──────────────────────┐
  │ object_module_mapping │     │ process_module_assign│
  ├───────────────────────┤     ├──────────────────────┤
  │ id (PK)               │     │ id (PK)              │
  │ tenant_id (FK)        │     │ tenant_id (FK)       │
  │ target_type           │     │ module_id (FK)       │
  │ target_id             │     │ is_applicable        │
  │ module_id (FK)        │     │ non_applicability_just│
  │ applicability         │     │ assigned_by (FK)     │
  │ rationale             │     │ assigned_at          │
  │ selected_by_user (FK) │     │ UQ(tenant,module)    │
  │ selected_at           │     └──────────────────────┘
  └───────────────────────┘
```

## IMR

```
  ┌──────────────┐     ┌────────────────────────┐     ┌───────────────────┐
  │asset_module  │     │       imr_items        │     │ bp_module_mappings│
  │ _mappings    │     ├────────────────────────┤     ├───────────────────┤
  ├──────────────┤     │ id (PK)                │     │                   │
  │ id (PK)      │1   N│ tenant_id (FK)         │N   1│ id (PK)           │
  └──────┬───────┘     │ asset_module_mapping   │     └─────────┬─────────┘
         │             │ bp_module_mapping      │◄──────────────┘
         │             │ measure_id (FK)        │
         │             │ is_process_module_meas  │
         │             │ pearo_status           │ (P/E/A/R/O)
         │             │ implementation_desc     │
         │             │ non_impl_justification  │
         │             │ partial_scope_desc      │
         │             │ responsible_user_id(FK) │
         │             │ due_date               │
         │             │ next_review_date       │
         │             │ priority               │ (P1/P2/P3)
         │             │ risk_acceptance_approver│
         │             │ risk_acceptance_date   │
         │             │ verification_method    │
         │             │ last_verified_at       │
         │             │ imr_snapshot_id (FK)   │
         │             │ created_by (FK)        │
         │             │ updated_by (FK)        │
         │             │ status_changed_at      │
         │             │ requirement_profile    │
         │             │ todo_description       │
         │             │ cost_eur               │
         │             │ deleted_at             │
         │             │ deleted_by             │
         │             │ created_at / updated_at │
         │             └────────────┬───────────┘
         │                          │N
         │                          │
         │                 ┌────────┴─────────┐
         │                 │  imr_snapshots   │
         │                 ├──────────────────┤
         │                 │ id (PK)          │
         │                 │ tenant_id (FK)   │
         │                 │ prot_mode_sel(FK)│
         │                 │ label            │
         │                 │ description      │
         │                 │ is_current       │
         │                 │ item_count       │
         │                 │ created_by (FK)  │
         │                 │ created_at       │
         │                 │ restored_from    │
         │                 └──────────────────┘

  ┌──────────────────────────────┐
  │ implementation_plan_items    │  (legacy IMR)
  ├──────────────────────────────┤
  │ id (PK)                      │
  │ tenant_id (FK)               │
  │ measure_id (FK)              │
  │ target_type / target_id      │
  │ owner_user_id (FK)           │
  │ status                       │
  │ priority                     │
  │ due_date                     │
  │ implementation_comment       │
  │ verification_method          │
  │ accepted_risk_id             │
  │ created_at / updated_at      │
  └──────────────────────────────┘
```

## Risk Register

```
  ┌──────────────┐     ┌─────────────────────┐     ┌──────────────┐
  │    risks     │     │ risk_measure_links  │     │  imr_items   │
  ├──────────────┤     ├─────────────────────┤     ├──────────────┤
  │ id (PK)      │1   N│ id (PK)             │N   1│ id (PK)      │
  │ tenant_id(FK)│     │ tenant_id (FK)      │     └──────────────┘
  │ title        │─────│ risk_id (FK)        │
  │ scenario     │     │ imr_item_id (FK)    │─────┘
  │ target_type  │     │ measure_id (FK)     │
  │ target_id    │     │ custom_measure_name │
  │ threat       │     │ custom_measure_desc │
  │ vulnerability│     │ created_at          │
  │ likelihood   │     └─────────────────────┘
  │ impact       │
  │ risk_level   │
  │ treatment    │
  │ owner_user(FK)│
  │ status       │
  │ review_date  │
  │ threat_id    │
  │ asset_id     │
  │ bp_id        │
  │ likelihood_scr│ (0-3)
  │ impact_score │ (0-3)
  │ risk_score   │ (GENERATED: likelihood*impact)
  │ risk_rating  │
  │ treatment_type│
  │ residual_risk │
  │ accepted_by  │
  │ accepted_at  │
  │ deleted_at   │
  │ deleted_by   │
  └──────────────┘
```

## Evidence

```
  ┌──────────────┐     ┌─────────────────────┐
  │  evidences   │     │   evidence_links    │
  ├──────────────┤     ├─────────────────────┤
  │ id (PK)      │1   N│ id (PK)             │
  │ tenant_id(FK)│     │ tenant_id (FK)      │
  │ title        │─────│ evidence_id (FK)    │
  │ evidence_type│     │ target_type         │ (polymorphic)
  │ storage_uri  │     │ target_id           │
  │ external_url │     │ link_type           │
  │ file_hash    │     └─────────────────────┘
  │ version      │
  │ owner_user(FK)│
  │ valid_from   │
  │ valid_until  │
  │ review_due   │
  │ file_size    │
  │ mime_type    │
  │ download_ cnt│
  │ deleted_at   │
  │ deleted_by   │
  │ created_at   │
  └──────────────┘
```
