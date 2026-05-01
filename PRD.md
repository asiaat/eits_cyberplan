# Project Document: E-ITS Management System

## 1. Project Objective

Build a web-based E-ITS information security management and compliance system that helps an organization map business processes, assets, risks, E-ITS baseline modules, security measures, the Information Security Measures Implementation Plan (IMR), roles, responsibilities, evidence, and audit readiness.

The solution must be a practical working tool for the information security manager, management board, process owners, IT owners, and auditors. The core value of the system is that E-ITS implementation will no longer be managed across scattered Excel files, Word documents, and separate evidence folders, but will instead be traceable, versioned, auditable, and managed in one application.

## 2. Recommended Technical Approach

- Frontend: React.js + TypeScript
- UI framework: Tailwind CSS + shadcn/ui or MUI
- Backend API: Python FastAPI
- Database: PostgreSQL
- ORM and migrations: SQLAlchemy + Alembic
- Background jobs: Celery or RQ + Redis
- Files and evidence: S3-compatible storage, for example MinIO or AWS S3
- Authentication: OpenID Connect / Keycloak / Azure AD / Google Workspace; local user management may be used in the MVP
- Authorization: role-based access control, later extended with object-level access control
- Audit log: append-only event log in the database
- Deployment: Docker Compose for MVP, later Kubernetes or managed PaaS

## 3. Product Vision

The system is an E-ITS workspace where a user can:

1. create an organization and protection scope;
2. describe business processes;
3. add assets, information systems, services, components, and data collections;
4. link assets to business processes;
5. determine protection needs for confidentiality, integrity, and availability;
6. import and manage E-ITS catalog data;
7. map target objects to baseline modules;
8. create a risk register;
9. link risks with measures and IMR tasks;
10. manage implementation status, owners, deadlines, and evidence for security measures;
11. monitor management dashboards, audit readiness, and gaps;
12. export reports for audits, management review, and work planning.

## 4. Main User Roles

### System Administrator

- manages organizations, users, roles, integrations, and general settings;
- imports E-ITS catalog versions;
- configures system security settings.

### Information Security Manager

- leads the E-ITS implementation process;
- approves the protection scope, objectives, roles, and responsibilities;
- manages the risk register, IMR, and reports;
- prepares management reviews and audits.

### Process Owner

- describes the business process;
- confirms the protection need of the process;
- links the process with assets and services;
- completes IMR tasks assigned to them.

### Asset Owner

- is responsible for the asset description, criticality, and relationships;
- adds evidence and confirms implementation of measures within the scope of their asset.

### Auditor / Viewer

- can view evidence, measure statuses, the risk register, and audit views;
- can add observations or nonconformities;
- cannot modify base data without the required permission.

## 5. MVP Scope

The purpose of the MVP is to create a working system that enables one organization to manage the core E-ITS process from mapping assets and processes to IMR tasks and evidence.

### MVP Functions

1. Organizations and users
   - organization creation;
   - user creation;
   - roles: admin, information security manager, process owner, asset owner, auditor;
   - role-based access control.

2. E-ITS catalog import
   - import E-ITS catalog/modules/measures from a file;
   - store catalog versions;
   - search modules and measures;
   - maintain module-measure relationships.

3. Business processes
   - add a process;
   - assign a process owner;
   - description, objective, inputs, outputs;
   - related assets;
   - protection need for C/I/A.

4. Asset register
   - asset type: business process, information system, application, server, data collection, network component, service, physical location, other;
   - owner;
   - criticality;
   - relationships with other assets;
   - related business processes;
   - protection need for C/I/A.

5. Module mapping
   - user can assign E-ITS modules to an asset or process;
   - the system stores the rationale for why a module was selected or excluded;
   - selecting a module creates the related set of security measures.

6. IMR: Information Security Measures Implementation Plan
   - measure list;
   - owner;
   - deadline;
   - status: not started, in progress, implemented, not applicable, accepted by exception;
   - priority;
   - comments;
   - evidence;
   - audit trail.

7. Risk register
   - risk scenario;
   - related asset/process;
   - threat/vulnerability;
   - impact;
   - likelihood;
   - risk level;
   - risk treatment: reduce, accept, avoid, transfer/share;
   - related measures and IMR tasks.

8. Evidence management
   - add a document or URL;
   - link evidence to a measure, asset, risk, or IMR task;
   - validity date;
   - version;
   - owner;
   - review deadline.

9. Dashboards
   - IMR completion percentage;
   - overdue tasks;
   - high risks;
   - implemented measures without evidence;
   - overall audit readiness score;
   - heatmap of protection needs and risks.

10. Export
   - IMR export as CSV/XLSX;
   - audit package export as ZIP;
   - management report in PDF/HTML format.

## 6. Out of MVP Scope, but Planned for Later Stages

- Active Directory / Entra ID / LDAP synchronization;
- Jira or Azure DevOps integration for IMR tasks;
- Estonian ID-card, Smart-ID, or Mobile-ID authentication;
- multi-organization tenant management;
- automatic asset import from CMDB, cloud platforms, or network scanners;
- AI-assisted module recommendations;
- AI-assisted risk scenario drafts;
- automatic generation of audit questionnaires;
- document content analysis to identify which measure a document could support as evidence;
- comparison between two versioned E-ITS catalogs;
- exception and risk acceptance workflow with management approval.

## 7. Core Data Model

### tenants

- id
- name
- registry_code
- created_at
- updated_at

### users

- id
- email
- name
- auth_provider
- is_active
- created_at

### roles

- id
- code
- name
- description

### memberships

- id
- tenant_id
- user_id
- role_id

### business_processes

- id
- tenant_id
- name
- owner_user_id
- description
- purpose
- inputs
- outputs
- status
- confidentiality_need
- integrity_need
- availability_need
- created_at
- updated_at

### assets

- id
- tenant_id
- name
- asset_type
- owner_user_id
- description
- criticality
- confidentiality_need
- integrity_need
- availability_need
- lifecycle_status
- created_at
- updated_at

### asset_relations

- id
- tenant_id
- source_asset_id
- target_asset_id
- relation_type
- description

### process_assets

- id
- tenant_id
- business_process_id
- asset_id
- relation_description

### eits_catalog_versions

- id
- version
- source_name
- source_file_hash
- imported_at
- active

### eits_modules

- id
- catalog_version_id
- code
- name
- category
- description
- module_type
- source_url

### eits_measures

- id
- catalog_version_id
- code
- title
- description
- measure_level
- responsible_role
- implementation_guidance

### eits_module_measures

- id
- module_id
- measure_id

### object_module_mappings

- id
- tenant_id
- target_type
- target_id
- module_id
- applicability
- rationale
- selected_by_user_id
- selected_at

### implementation_plan_items

- id
- tenant_id
- measure_id
- target_type
- target_id
- owner_user_id
- status
- priority
- due_date
- implementation_comment
- verification_method
- accepted_risk_id
- created_at
- updated_at

### risks

- id
- tenant_id
- title
- scenario
- target_type
- target_id
- threat
- vulnerability
- likelihood
- impact
- risk_level
- treatment
- owner_user_id
- status
- review_date

### risk_measures

- id
- risk_id
- measure_id
- implementation_plan_item_id

### evidences

- id
- tenant_id
- title
- evidence_type
- storage_uri
- external_url
- version
- owner_user_id
- valid_from
- valid_until
- review_due_date
- created_at

### evidence_links

- id
- tenant_id
- evidence_id
- target_type
- target_id

### audit_logs

- id
- tenant_id
- actor_user_id
- action
- entity_type
- entity_id
- before_json
- after_json
- created_at

### comments

- id
- tenant_id
- entity_type
- entity_id
- author_user_id
- body
- created_at

## 8. API Design

### Authentication and users

- POST /auth/login
- POST /auth/logout
- GET /auth/me
- GET /users
- POST /users
- PATCH /users/{id}
- GET /roles
- POST /memberships

### Organization and settings

- GET /tenants/current
- PATCH /tenants/current
- GET /settings
- PATCH /settings

### E-ITS catalog

- POST /catalog/import
- GET /catalog/versions
- GET /catalog/modules
- GET /catalog/modules/{id}
- GET /catalog/measures
- GET /catalog/measures/{id}
- GET /catalog/modules/{id}/measures

### Business processes

- GET /business-processes
- POST /business-processes
- GET /business-processes/{id}
- PATCH /business-processes/{id}
- DELETE /business-processes/{id}
- POST /business-processes/{id}/assets
- DELETE /business-processes/{id}/assets/{asset_id}

### Assets

- GET /assets
- POST /assets
- GET /assets/{id}
- PATCH /assets/{id}
- DELETE /assets/{id}
- POST /assets/{id}/relations
- DELETE /assets/{id}/relations/{relation_id}

### Module mapping

- GET /mappings?target_type=&target_id=
- POST /mappings
- PATCH /mappings/{id}
- DELETE /mappings/{id}
- POST /mappings/suggest

### IMR

- GET /implementation-plan
- POST /implementation-plan/generate
- GET /implementation-plan/{id}
- PATCH /implementation-plan/{id}
- POST /implementation-plan/{id}/evidence
- POST /implementation-plan/{id}/comments
- POST /implementation-plan/export

### Risks

- GET /risks
- POST /risks
- GET /risks/{id}
- PATCH /risks/{id}
- DELETE /risks/{id}
- POST /risks/{id}/measures
- POST /risks/{id}/review

### Evidence

- GET /evidences
- POST /evidences
- GET /evidences/{id}
- PATCH /evidences/{id}
- DELETE /evidences/{id}
- POST /evidences/{id}/links

### Dashboards and reports

- GET /dashboard/summary
- GET /dashboard/imr-progress
- GET /dashboard/risk-heatmap
- GET /reports/management-review
- GET /reports/audit-readiness
- POST /reports/audit-package

## 9. Frontend Views

### 9.1 Login

- OIDC login or local login;
- organization selection if the user belongs to multiple organizations.

### 9.2 Home / Dashboard

- E-ITS implementation status;
- IMR progress chart;
- high risks;
- overdue tasks;
- measures without evidence;
- audit readiness score.

### 9.3 Business Processes

- table view;
- process detail;
- related assets;
- protection need assessment for C/I/A;
- related risks;
- related measures.

### 9.4 Assets

- asset register;
- filters by type, owner, criticality, and protection need;
- relationship graph;
- asset detail;
- related modules and measures.

### 9.5 E-ITS Catalog

- module search;
- measure search;
- categories;
- catalog versions;
- module detail with related measures.

### 9.6 Mapping

- view of selected modules for the chosen asset or process;
- recommended modules;
- user decision: applicable, not applicable, requires decision;
- rationale for applying or excluding a module.

### 9.7 Risk Register

- risk table;
- heatmap;
- risk scenario form;
- relationships to assets, processes, measures, and IMR tasks;
- risk treatment decisions.

### 9.8 IMR

- implementation action plan;
- statuses;
- owners;
- deadlines;
- evidence;
- comments;
- bulk editing;
- exports.

### 9.9 Evidence and Documents

- evidence register;
- document upload;
- URL references;
- validity and review deadlines;
- evidence links to measures and risks.

### 9.10 Audit View

- requirements and measures;
- completed/not completed status;
- related evidence;
- deviations;
- audit package export.

### 9.11 Admin

- users and roles;
- organization settings;
- catalog import;
- integrations;
- audit log.

## 10. Agentic Harness: Work Allocation for AI Agents

This project can be developed in an agentic harness style, where each agent has a clear responsibility and a verifiable output.

### Agent 1: Product Owner Agent

Task: maintain product scope, user stories, priorities, and acceptance criteria.

Input:

- this project document;
- E-ITS requirements document;
- E-ITS support application / Volur data model or exported data;
- Cybsis-like functional inspiration.

Output:

- backlog;
- user stories;
- acceptance criteria;
- sprint objectives.

### Agent 2: Domain Analyst Agent

Task: model the E-ITS domain into a form suitable for development.

Output:

- entity glossary;
- process flow: protection scope → target objects → protection need → modules → measures → IMR → evidence → audit;
- data field specifications;
- domain rules.

### Agent 3: Database Architect Agent

Task: create the PostgreSQL schema, indexes, migrations, and data versioning logic.

Output:

- ERD;
- Alembic migrations;
- seed/import scripts;
- database constraints;
- audit log triggers or application-level logic.

### Agent 4: Backend API Agent

Task: build FastAPI services.

Output:

- API endpoints;
- Pydantic schemas;
- SQLAlchemy models;
- service layer;
- tests;
- OpenAPI documentation.

### Agent 5: Frontend Agent

Task: build the React user interface.

Output:

- routing;
- views;
- forms;
- tables;
- dashboards;
- API client;
- state management;
- UI tests.

### Agent 6: Security Agent

Task: review the security of the system itself.

Output:

- threat model;
- RBAC/ABAC controls;
- secure file management requirements;
- audit log requirements;
- OWASP checklist;
- security test scenarios.

### Agent 7: QA Agent

Task: prepare the test plan and automated tests.

Output:

- unit tests;
- API integration tests;
- frontend e2e tests;
- regression suite;
- acceptance tests for user stories.

### Agent 8: DevOps Agent

Task: set up development, test, and production environments.

Output:

- Docker Compose;
- CI/CD pipeline;
- sample environment variables;
- backup and restore instructions;
- logging and monitoring.

## 11. Agentic Harness Rules

1. Each agent makes changes only within its area of responsibility.
2. Every change must include a testable output.
3. Any data model change must go through the Database Architect Agent.
4. Any API change must update the OpenAPI schema.
5. Any frontend change must use only documented API endpoints.
6. The Security Agent reviews changes related to authentication, authorization, evidence storage, and audit logging.
7. The Product Owner Agent confirms that the result meets the business need.
8. The QA Agent confirms that acceptance criteria have been met.

## 12. User Stories for the MVP

### EPIC 1: Organization and Access Control

US-1: As an admin, I want to create an organization so that E-ITS data can be grouped under it.

Acceptance criteria:

- the organization has a name and registry code;
- the organization can be edited;
- all data is linked to the organization through tenant_id.

US-2: As an admin, I want to assign a role to a user so that they can see only the information they need.

Acceptance criteria:

- a user can have multiple roles;
- the role controls API access;
- an unauthorized request returns 403.

### EPIC 2: E-ITS Catalog

US-3: As an admin, I want to import an E-ITS catalog version so that the system uses the official module and measure base.

Acceptance criteria:

- the import stores the catalog version;
- modules have a code, name, description, and type;
- measures have a code, title, description, and responsible role;
- duplicate import of the same version is prevented or clearly versioned.

### EPIC 3: Business Processes and Assets

US-4: As an information security manager, I want to add a business process so that its protection need and asset relationships can be assessed.

Acceptance criteria:

- the process has an owner;
- C/I/A protection needs can be assigned to the process;
- assets can be added to the process.

US-5: As an asset owner, I want to add an asset and its relationships so that it is clear what must be protected.

Acceptance criteria:

- the asset has a type, owner, and description;
- the asset can be linked to another asset;
- the asset can be linked to a business process.

### EPIC 4: Modules and Measures

US-6: As an information security manager, I want to assign E-ITS modules to an asset so that an implementation plan for measures can be created.

Acceptance criteria:

- selecting a module creates the related measures as IMR candidates;
- the user can add a rationale;
- the user can mark a module as not applicable.

### EPIC 5: IMR

US-7: As an information security manager, I want to generate an IMR based on selected modules so that I receive an implementation task plan.

Acceptance criteria:

- the IMR includes measures, target object, owner, and deadline;
- tasks have statuses;
- a comment and evidence can be added to a task.

US-8: As a process owner, I want to see only my own tasks so that I can focus on my responsibilities.

Acceptance criteria:

- the user can see IMR tasks assigned to them;
- the user can change allowed statuses;
- all changes are logged.

### EPIC 6: Risks

US-9: As an information security manager, I want to add a risk scenario so that situations outside baseline protection or with higher protection needs can be documented.

Acceptance criteria:

- the risk has a related asset or process;
- the risk has impact, likelihood, and risk level;
- the risk is linked to measures or IMR tasks.

### EPIC 7: Evidence and Audit

US-10: As an auditor, I want to see measure evidence in one view so that I can verify implementation.

Acceptance criteria:

- related evidence is shown next to the measure;
- evidence has validity and owner;
- the audit view shows completed and incomplete measures.

## 13. Development Phases

### Phase 0: Analysis and Technical Foundation, 1–2 weeks

- final scope;
- data model approval;
- repository structure;
- Docker Compose;
- FastAPI skeleton;
- React skeleton;
- PostgreSQL and migrations;
- CI pipeline.

### Phase 1: Catalog and Users, 2 weeks

- authentication;
- users and roles;
- E-ITS catalog import;
- module and measure views.

### Phase 2: Business Processes and Assets, 2–3 weeks

- process CRUD;
- asset CRUD;
- asset relationships;
- protection need assessment;
- process and asset detail views.

### Phase 3: Module Mapping and IMR, 3 weeks

- module selection;
- measure generation;
- IMR action plan;
- statuses, owners, deadlines;
- comments.

### Phase 4: Risks and Evidence, 3 weeks

- risk register;
- risk level calculation;
- evidence uploads and URLs;
- linking evidence to measures, risks, and assets.

### Phase 5: Dashboards and Audit View, 2 weeks

- management dashboard;
- audit view;
- exports;
- reports.

### Phase 6: Stabilization and Pilot, 2–4 weeks

- QA;
- security tests;
- performance tests;
- pilot organization data entry;
- feedback;
- MVP release.

## 14. Security Requirements for the System Itself

1. All requests must be authenticated, except login and health check.
2. All tenant data must be isolated through tenant_id.
3. API permissions must be checked server-side, not only in the UI.
4. All important changes must be written to the audit log.
5. Evidence files must have private access.
6. File uploads must be checked for size, type, and malware risk.
7. Passwords, if local login is used, must be hashed with Argon2 or bcrypt.
8. MFA is recommended at least for admins and information security managers.
9. The database must be backed up and restore must be tested.
10. Passwords, session tokens, or sensitive evidence content must not be written to logs.
11. TLS must be used in production.
12. Sessions and JWT configuration must use short lifetimes and secure refresh mechanisms.

## 15. Import Strategy from E-ITS / Volur Source

The MVP should include a separate import pipeline:

1. Input file: E-ITS support application HTML, JSON, or an official catalog export format.
2. Parser identifies the catalog version.
3. Parser extracts modules, measures, roles, categories, and relationships.
4. Import validates mandatory fields.
5. Import creates staging tables.
6. Admin approves the import.
7. The approved version becomes active.
8. The old version remains available so that existing IMR tasks do not change unexpectedly.

Important: The E-ITS catalog must be treated as versioned reference data, not user-entered content. Organization-specific implementation data must be stored separately from the catalog version, while referencing it.

## 16. AI-Assisted Functions for Later Stages

### 16.1 Module Recommendations

AI analyzes asset type, description, related processes, and protection need, then suggests likely E-ITS modules. The user confirms or rejects the suggestions.

### 16.2 Risk Scenario Drafts

AI prepares risk scenarios based on asset and process descriptions. The information security manager confirms, edits, or deletes them.

### 16.3 Evidence Suitability Assessment

AI reads a document summary and suggests which measure the document could support as evidence.

### 16.4 Management Report Generation

AI prepares a draft management review based on dashboard data.

### 16.5 Audit Gap Analysis

AI identifies measures that have the status implemented but are missing evidence, a review date, or an owner.

AI functions must not make automatic compliance decisions without human confirmation. They must be assistive, not final decision-makers.

## 17. MVP Definition of Done

The MVP is ready when:

- the user can log in;
- organization and roles work;
- the E-ITS catalog can be imported and searched;
- business processes and assets can be added;
- protection needs can be assigned;
- assets can be linked to processes;
- E-ITS modules can be selected;
- IMR tasks can be generated;
- risks can be added;
- evidence can be added;
- the dashboard displays key metrics;
- the audit view displays relationships between measures, statuses, and evidence;
- all critical changes are in the audit log;
- database migrations and automated tests run in CI.

## 18. Project Delivery Risks

### Risk: The E-ITS catalog structure changes or the source is not machine-readable

Mitigation: build the import layer as a separate module, use staging tables, and include a manual approval step.

### Risk: The MVP becomes too large

Mitigation: keep the MVP limited to business processes, assets, catalog, modules, IMR, risks, evidence, and dashboard. Leave integrations for the next stage.

### Risk: Compliance decisions are too complex to automate

Mitigation: the system does not decide compliance automatically; it helps link data, manage workflows, and present evidence.

### Risk: Evidence contains sensitive data

Mitigation: strong role-based access, private file storage, audit log, and encrypted storage.

### Risk: Users do not maintain data consistently

Mitigation: tasks, deadlines, dashboards, notifications, and mandatory field validation.

## 19. Initial Backlog for Developers

1. Create a monorepo or two repositories: frontend and backend.
2. Create Docker Compose: frontend, backend, postgres, redis, minio.
3. Create FastAPI skeleton with a health check endpoint.
4. Create React skeleton with routing.
5. Add SQLAlchemy, Alembic, and the first migration.
6. Create user, role, and organization tables.
7. Add MVP-level JWT/OIDC authentication.
8. Add RBAC dependency in FastAPI.
9. Create E-ITS catalog tables.
10. Build the first version of the catalog importer.
11. Create module and measure API.
12. Create frontend views for modules and measures.
13. Create business process CRUD.
14. Create asset CRUD.
15. Create process-asset relationships.
16. Add protection need fields and validation.
17. Create module mapping API and UI.
18. Create IMR generation service.
19. Create IMR table and detail view.
20. Add comments and statuses.
21. Add evidence upload to MinIO.
22. Add evidence relationships.
23. Create risk register.
24. Add dashboard API.
25. Add audit log.
26. Add CSV/XLSX export.
27. Add audit view.
28. Write API tests.
29. Write frontend e2e tests.
30. Create pilot data seed.

## 20. Success Metrics

- 100% of importable E-ITS catalog modules and measures are searchable;
- at least 90% of user workflows can be completed without Excel;
- IMR task statuses and owners are visible on the dashboard;
- the audit view shows related evidence or gaps for each implemented measure;
- the management report can be generated with one click;
- all critical changes are in the audit log;
- the pilot organization can enter at least one complete protection scope, 5 business processes, 20 assets, 30 implementation plan tasks, and related evidence.

## 21. Next Practical Step

Confirm the MVP scope and create two technical artifacts:

1. PostgreSQL ERD with tables, relationships, and indexes.
2. First OpenAPI specification for the core flows: users, catalog, business processes, assets, module mapping, IMR, risks, evidence, and dashboards.
