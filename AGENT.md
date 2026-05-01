# AGENT.md — E-ITS Management System Development Guide

This file defines the operating rules, repository structure, development environment, coding standards, and SOPs for AI-assisted development of the E-ITS Management System using tools such as OpenCode or other coding agents.

The goal is to make the project safe, auditable, and easy to continue across multiple agent sessions.

---

## 1. Project Summary

Build a web-based E-ITS management system for handling:

- organizations and tenants;
- users, roles, and permissions;
- E-ITS catalog versions, modules, and measures;
- business processes;
- assets and asset relations;
- protection needs for confidentiality, integrity, and availability;
- module mappings;
- implementation plan items / IMR;
- risks and risk treatment;
- evidence and document links;
- dashboards, reports, and audit readiness.

Recommended stack:

- Frontend: React + TypeScript
- Backend: Python + FastAPI
- Database: PostgreSQL
- ORM: SQLAlchemy
- Migrations: Alembic
- Background jobs: Redis + RQ or Celery
- Object storage: MinIO or S3-compatible storage
- Local orchestration: Docker Compose
- Tests: Pytest, Vitest, Playwright

---

## 2. Core Development Principle

Do not optimize for fast code generation only.

Optimize for:

1. clear domain model;
2. traceability;
3. auditability;
4. secure defaults;
5. repeatable local setup;
6. automated tests;
7. migration-safe database changes;
8. minimal hidden assumptions.

Every meaningful change must be reviewable through code, tests, migrations, and documentation.

---

## 3. Recommended Repository Structure

Use a monorepo.

```text
eits-management-system/
├── AGENT.md
├── README.md
├── Makefile
├── docker-compose.yml
├── docker-compose.override.yml
├── .env.example
├── .gitignore
├── docs/
│   ├── architecture/
│   │   ├── overview.md
│   │   ├── erd.md
│   │   ├── api-design.md
│   │   └── security-model.md
│   ├── domain/
│   │   ├── glossary.md
│   │   ├── eits-process.md
│   │   ├── catalog-import.md
│   │   └── imr-workflow.md
│   ├── sop/
│   │   ├── local-development.md
│   │   ├── database-migrations.md
│   │   ├── testing.md
│   │   ├── pull-request.md
│   │   ├── release.md
│   │   ├── backup-restore.md
│   │   └── incident-response.md
│   └── decisions/
│       └── ADR-0001-monorepo.md
├── backend/
│   ├── pyproject.toml
│   ├── alembic.ini
│   ├── alembic/
│   │   ├── env.py
│   │   └── versions/
│   ├── app/
│   │   ├── main.py
│   │   ├── api/
│   │   │   ├── deps.py
│   │   │   └── v1/
│   │   │       ├── router.py
│   │   │       ├── auth.py
│   │   │       ├── users.py
│   │   │       ├── tenants.py
│   │   │       ├── catalog.py
│   │   │       ├── business_processes.py
│   │   │       ├── assets.py
│   │   │       ├── mappings.py
│   │   │       ├── implementation_plan.py
│   │   │       ├── risks.py
│   │   │       ├── evidences.py
│   │   │       ├── dashboard.py
│   │   │       └── reports.py
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   ├── security.py
│   │   │   ├── permissions.py
│   │   │   └── audit.py
│   │   ├── db/
│   │   │   ├── session.py
│   │   │   ├── base.py
│   │   │   └── init_db.py
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── services/
│   │   ├── repositories/
│   │   ├── workers/
│   │   └── importers/
│   │       ├── eits_catalog_importer.py
│   │       └── volur_html_parser.py
│   └── tests/
│       ├── unit/
│       ├── integration/
│       └── fixtures/
├── frontend/
│   ├── package.json
│   ├── vite.config.ts
│   ├── tsconfig.json
│   ├── index.html
│   ├── src/
│   │   ├── main.tsx
│   │   ├── app/
│   │   ├── routes/
│   │   ├── pages/
│   │   │   ├── DashboardPage.tsx
│   │   │   ├── CatalogPage.tsx
│   │   │   ├── BusinessProcessesPage.tsx
│   │   │   ├── AssetsPage.tsx
│   │   │   ├── ImplementationPlanPage.tsx
│   │   │   ├── RisksPage.tsx
│   │   │   ├── EvidencesPage.tsx
│   │   │   ├── AuditViewPage.tsx
│   │   │   └── AdminPage.tsx
│   │   ├── components/
│   │   ├── features/
│   │   ├── lib/
│   │   │   ├── api-client.ts
│   │   │   ├── auth.ts
│   │   │   └── permissions.ts
│   │   ├── hooks/
│   │   └── types/
│   └── tests/
│       ├── unit/
│       └── e2e/
├── infra/
│   ├── docker/
│   │   ├── backend.Dockerfile
│   │   └── frontend.Dockerfile
│   ├── nginx/
│   ├── postgres/
│   └── minio/
├── scripts/
│   ├── dev-bootstrap.sh
│   ├── seed_demo_data.py
│   ├── export_openapi.py
│   └── check_quality.sh
└── data/
    ├── imports/
    │   └── .gitkeep
    └── samples/
        └── .gitkeep
```

---

## 4. Local Development Environment

### 4.1 Required Tools

Install locally:

- Git
- Docker
- Docker Compose
- Python 3.11+
- Node.js LTS
- pnpm or npm
- Make
- PostgreSQL client tools, optional but useful

### 4.2 Environment Variables

Create `.env` from `.env.example`.

Example:

```env
APP_ENV=local
APP_NAME=eits-management-system

POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_DB=eits
POSTGRES_USER=eits
POSTGRES_PASSWORD=eits_dev_password

DATABASE_URL=postgresql+psycopg://eits:eits_dev_password@postgres:5432/eits

REDIS_URL=redis://redis:6379/0

MINIO_ENDPOINT=minio:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET=eits-evidence
MINIO_SECURE=false

JWT_SECRET_KEY=change-me-in-local-only
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

BACKEND_CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

### 4.3 Docker Compose Services

The local environment should include:

```text
frontend    React dev server
backend     FastAPI app
postgres    PostgreSQL database
redis       queue/cache service
minio       local object storage
mailhog     optional local email capture
```

Recommended local ports:

```text
Frontend:       http://localhost:5173
Backend API:    http://localhost:8000
OpenAPI docs:   http://localhost:8000/docs
PostgreSQL:     localhost:5432
MinIO console:  http://localhost:9001
```

### 4.4 Standard Setup Commands

From repository root:

```bash
cp .env.example .env
docker compose up -d postgres redis minio
make backend-install
make frontend-install
make migrate
make seed
make dev
```

Alternative full Docker mode:

```bash
cp .env.example .env
docker compose up --build
```

---

## 5. Makefile Contract

Agents should prefer Make targets over ad-hoc commands.

Required targets:

```makefile
help:
setup:

seed:
test:
test-backend:
test-frontend:
lint:
format:
typecheck:
quality:
openapi:
down:
clean:
```

Expected behavior:

```bash
make setup       # install dependencies and prepare local env
make dev         # run backend and frontend in dev mode
make migrate     # apply Alembic migrations
make migration   # create a new Alembic migration, requires MESSAGE
make seed        # seed demo data
make test        # run all tests
make quality     # lint, format check, typecheck, tests
make openapi     # export OpenAPI JSON
```

Migration example:

```bash
make migration MESSAGE="create assets table"
```

---

## 6. OpenCode / Coding Agent Usage

### 6.1 Recommended Startup Prompt

Use this when starting a new OpenCode session:

```text
You are working on the E-ITS Management System.

First read AGENT.md, README.md, docs/architecture/overview.md, and docs/domain/glossary.md.

Follow the repository SOPs. Do not invent project structure. Do not change database schema without creating an Alembic migration and tests. Do not bypass RBAC or tenant isolation. All API changes must update schemas and tests. All frontend API calls must use the shared API client.

Before coding, summarize the task, affected files, and test plan.
After coding, run or describe the relevant tests.
```

### 6.2 Standard Task Prompt Template

```text
Task:
[Describe the change]

Context:
[Relevant domain object, API, UI view, or bug]

Constraints:
- Follow AGENT.md.
- Keep changes minimal.
- Add or update tests.
- Update docs if behavior changes.
- Do not introduce new dependencies without explaining why.

Expected output:
- Code changes.
- Migration if needed.
- Tests.
- Short implementation summary.
```

### 6.3 Agent Completion Checklist

Before finishing a task, the coding agent must report:

```text
Changed files:
- ...

Database changes:
- yes/no
- migration file: ...

Tests:
- added/updated: ...
- command run: ...
- result: ...

Security considerations:
- tenant isolation checked
- RBAC checked
- audit logging checked where relevant

Documentation:
- updated/not needed
```

---

## 7. Coding Directives

### 7.1 General

- Prefer simple code over clever abstractions.
- Use explicit names for domain concepts.
- Keep E-ITS terms consistent across backend, frontend, database, and docs.
- Do not mix Estonian and English identifiers in code.
- Use English for code identifiers.
- UI labels may support Estonian later via i18n.
- Avoid global mutable state.
- Avoid hidden magic in services.
- Validate all external input.

### 7.2 Backend Directives

- FastAPI routers live in `backend/app/api/v1/`.
- SQLAlchemy models live in `backend/app/models/`.
- Pydantic schemas live in `backend/app/schemas/`.
- Business logic lives in `backend/app/services/`.
- Database access helpers live in `backend/app/repositories/`.
- Do not put business logic directly in route handlers.
- All tenant-scoped queries must filter by `tenant_id`.
- All write operations must check permissions server-side.
- Critical writes must create audit log entries.
- Never return internal IDs across tenants.
- Never expose secrets, file storage credentials, or raw JWT values.

### 7.3 Frontend Directives

- Use TypeScript.
- Use the shared API client from `frontend/src/lib/api-client.ts`.
- Do not hardcode API URLs in components.
- Keep pages thin; put feature logic in `features/`.
- Use reusable table, form, status badge, and detail components.
- Handle loading, empty, error, and unauthorized states.
- Do not hide backend authorization errors; show a safe user-facing message.
- All forms must validate required fields before submission.

### 7.4 Database Directives

- Every schema change requires an Alembic migration.
- Migrations must be reversible where practical.
- Use foreign keys for core domain relations.
- Add indexes for common filters:
  - `tenant_id`
  - `owner_user_id`
  - `status`
  - `catalog_version_id`
  - `target_type`, `target_id`
  - `created_at`
- Use enum-like constraints carefully; prefer stable text codes when domain values may evolve.
- Do not delete catalog versions if implementation data references them.
- Prefer soft delete for user-created domain records that may be audit-relevant.

### 7.5 Security Directives

- Tenant isolation is mandatory.
- RBAC is mandatory.
- Audit logging is mandatory for important changes.
- Evidence files must be private by default.
- File uploads must validate type and size.
- Do not store secrets in Git.
- Do not log passwords, tokens, authorization headers, or file contents.
- Use parameterized queries through ORM.
- Use least-privilege service credentials.

---

## 8. Domain Directives

### 8.1 Core E-ITS Workflow

The product must support this workflow:

```text
Leadership commitment
→ ISMS scope / protection area
→ business processes
→ target objects and assets
→ protection needs: confidentiality, integrity, availability
→ security approach / baseline security mapping
→ E-ITS modules
→ E-ITS measures
→ implementation plan / IMR
→ responsibilities and deadlines
→ evidence
→ monitoring and improvement
→ audit readiness
```

### 8.2 Mandatory Domain Objects

Do not remove or merge these concepts without explicit architectural decision:

- Tenant / organization
- User
- Role
- Membership
- Business process
- Asset
- Asset relation
- E-ITS catalog version
- E-ITS module
- E-ITS measure
- Module-measure relation
- Object-module mapping
- Implementation plan item / IMR item
- Risk
- Evidence
- Evidence link
- Audit log
- Comment

### 8.3 Protection Need Values

Use stable values:

```text
normal
high
very_high
unknown
```

Display labels may be localized:

```text
normal      → normaalne
high        → suur
very_high   → väga suur
unknown     → määramata
```

### 8.4 IMR Status Values

Use stable values:

```text
not_started
in_progress
implemented
not_applicable
accepted_exception
needs_review
```

### 8.5 Risk Treatment Values

Use stable values:

```text
mitigate
accept
avoid
transfer
```

---

## 9. SOP: Creating a New Backend Endpoint

1. Confirm the domain object and permission requirement.
2. Add or update SQLAlchemy model if needed.
3. Add or update Alembic migration if database changes are needed.
4. Add or update Pydantic schemas.
5. Add repository functions.
6. Add service-layer logic.
7. Add route handler.
8. Add RBAC dependency.
9. Add tenant isolation.
10. Add audit logging for write operations.
11. Add tests:
    - successful request;
    - unauthorized request;
    - cross-tenant access denied;
    - validation error;
    - audit log if relevant.
12. Update OpenAPI export if required.
13. Update docs if behavior changed.

---

## 10. SOP: Creating a New Frontend Page

1. Confirm API endpoint exists.
2. Add route.
3. Add page component under `pages/`.
4. Add feature module under `features/` if logic is non-trivial.
5. Use shared API client.
6. Add loading state.
7. Add empty state.
8. Add error state.
9. Add permission-aware UI behavior.
10. Add form validation where needed.
11. Add unit or component tests.
12. Add Playwright e2e test for critical workflows.

---

## 11. SOP: Database Migration

1. Update SQLAlchemy model.
2. Create Alembic migration.

```bash
make migration MESSAGE="describe change"
```

3. Review generated migration manually.
4. Ensure downgrade is safe or explicitly documented.
5. Apply migration.

```bash
make migrate
```

6. Run backend tests.

```bash
make test-backend
```

7. If the migration changes seed data, update seed scripts.
8. Document impact in PR summary.

Never edit an already-applied migration in a shared branch unless the team has explicitly agreed.

---

## 12. SOP: E-ITS Catalog Import

Catalog import must be treated as a controlled data operation.

1. Place source files in `data/imports/`.
2. Parse into staging structures.
3. Validate:
   - catalog version exists;
   - module codes are unique within version;
   - measure codes are unique within version;
   - module-measure relations reference existing records;
   - required fields are present.
4. Store source file hash.
5. Create inactive catalog version.
6. Let admin review import summary.
7. Activate version only after confirmation.
8. Never mutate historical catalog versions in place.
9. Existing IMR items must continue referencing the catalog version from which they were generated.

Importer modules:

```text
backend/app/importers/eits_catalog_importer.py
backend/app/importers/volur_html_parser.py
```

---

## 13. SOP: IMR Generation

1. User selects target object:
   - business process;
   - asset;
   - system;
   - service;
   - location;
   - other supported object.
2. User maps E-ITS modules.
3. System resolves measures through module-measure relations.
4. System creates implementation plan items.
5. System avoids duplicates for same:
   - tenant;
   - target;
   - catalog version;
   - measure.
6. User assigns owner, priority, and due date.
7. Status starts as `not_started` unless explicitly set.
8. All generated items must be traceable to source module and catalog version.
9. Regeneration must not overwrite user status, comments, evidence, or accepted exceptions.

---

## 14. SOP: Evidence Management

1. Evidence may be:
   - uploaded file;
   - external URL;
   - text note;
   - reference to another system.
2. Evidence must have:
   - title;
   - owner;
   - type;
   - linked target;
   - creation timestamp.
3. Evidence should have:
   - valid from;
   - valid until;
   - review due date.
4. Evidence files are private by default.
5. Evidence links may point to:
   - IMR item;
   - measure;
   - risk;
   - asset;
   - business process.
6. Deleting evidence should be soft-delete unless it was uploaded by mistake and no audit-relevant process has used it.

---

## 15. SOP: Risk Register

1. Risk must be linked to a target object when possible.
2. Risk must include:
   - scenario;
   - threat;
   - vulnerability or cause;
   - likelihood;
   - impact;
   - risk level;
   - treatment;
   - owner;
   - status.
3. Risk can link to measures and IMR items.
4. Accepted risk must have:
   - rationale;
   - owner;
   - review date;
   - approval reference if available.
5. High and very high risks must appear on dashboard.

---

## 16. SOP: Audit Logging

Audit log is required for:

- user role changes;
- tenant settings changes;
- catalog activation;
- business process create/update/delete;
- asset create/update/delete;
- protection need changes;
- module mapping decisions;
- IMR item status changes;
- risk create/update/delete;
- risk acceptance;
- evidence upload/delete/linking;
- report or audit package generation, if relevant.

Audit log entry should contain:

```text
tenant_id
actor_user_id
action
entity_type
entity_id
before_json
after_json
created_at
```

Do not store secrets or raw file contents in audit logs.

---

## 17. SOP: Testing

### 17.1 Backend Tests

Required test classes:

- model tests;
- service tests;
- API integration tests;
- permission tests;
- tenant isolation tests;
- migration smoke test;
- importer tests.

Run:

```bash
make test-backend
```

### 17.2 Frontend Tests

Required tests:

- component tests for forms and tables;
- API client tests;
- permission rendering tests;
- e2e tests for critical workflows.

Run:

```bash
make test-frontend
```

### 17.3 Critical E2E Workflows

At minimum:

1. login;
2. create business process;
3. create asset;
4. link asset to business process;
5. set protection needs;
6. map E-ITS module;
7. generate IMR item;
8. update IMR status;
9. upload evidence;
10. create risk;
11. view dashboard;
12. open audit view.

---

## 18. SOP: Pull Request

Each PR must include:

```markdown
## Summary
What changed?

## Why
Why was this needed?

## Scope
What is included and what is not included?

## Database changes
- [ ] No database changes
- [ ] Migration included

## Security
- [ ] RBAC checked
- [ ] Tenant isolation checked
- [ ] Audit logging checked
- [ ] No secrets added

## Tests
Commands run and result.

## Screenshots
Required for UI changes.

## Documentation
Docs updated or not needed.
```

Do not merge if:

- tests fail;
- migration is missing for schema change;
- RBAC is bypassed;
- tenant isolation is not tested for tenant-scoped data;
- secrets are committed;
- generated files are committed without reason.

---

## 19. SOP: Release

1. Freeze scope.
2. Run full quality check.

```bash
make quality
```

3. Apply migrations in staging.
4. Run smoke tests.
5. Verify login and tenant isolation.
6. Verify catalog version.
7. Verify IMR and evidence workflows.
8. Create release notes.
9. Backup production database.
10. Deploy backend.
11. Run migrations.
12. Deploy frontend.
13. Run post-deploy smoke tests.
14. Monitor logs.

---

## 20. SOP: Backup and Restore

### Backup

- PostgreSQL backup daily.
- Object storage backup daily.
- Keep at least 30 days of backups in non-production policy; production policy may be stricter.
- Encrypt backups where possible.

### Restore Test

At least monthly:

1. restore database to test environment;
2. restore evidence bucket;
3. run application;
4. verify sample tenant data;
5. verify evidence download;
6. document result.

---

## 21. SOP: Incident Response for This Application

If a suspected security incident occurs:

1. Preserve logs.
2. Disable affected accounts if needed.
3. Rotate secrets if token or credential exposure is suspected.
4. Snapshot database and object storage metadata.
5. Identify affected tenants.
6. Review audit logs.
7. Contain issue.
8. Patch and test.
9. Document timeline.
10. Notify stakeholders according to legal and contractual requirements.

Do not delete logs during investigation.

---

## 22. Definition of Done

A task is done only when:

- implementation matches the requested scope;
- tests are added or updated;
- relevant tests pass;
- database migrations are included if needed;
- RBAC and tenant isolation are checked;
- audit logging is implemented where relevant;
- docs are updated if behavior changed;
- code is formatted and linted;
- no secrets or local-only files are committed.

---

## 23. Architecture Guardrails

### 23.1 Tenant Isolation

Every tenant-scoped table must have `tenant_id`.

Every tenant-scoped query must include tenant filtering.

Cross-tenant access must return either:

- 404 if object existence should not be disclosed;
- 403 if existence disclosure is acceptable and permission is missing.

Choose one pattern and keep it consistent.

### 23.2 Catalog Versioning

E-ITS catalog data is reference data.

Rules:

- catalog versions are immutable after activation;
- user implementation data references catalog version;
- activating a new version does not rewrite existing IMR items;
- migration between catalog versions must be an explicit workflow.

### 23.3 Auditability

The system must be able to answer:

- who changed this;
- when it changed;
- what changed;
- why it changed, if a rationale field exists;
- what evidence supports this status;
- which catalog version was used.

### 23.4 Human Approval for AI Features

AI may suggest:

- module mappings;
- risks;
- evidence links;
- report drafts.

AI must not silently approve:

- compliance status;
- risk acceptance;
- audit readiness;
- management approval;
- evidence validity.

Human confirmation is required.

---

## 24. Initial Implementation Order

Recommended first 30 development tasks:

1. Create repo structure.
2. Add Docker Compose.
3. Add `.env.example`.
4. Add Makefile.
5. Add FastAPI skeleton.
6. Add React skeleton.
7. Add PostgreSQL connection.
8. Add Alembic.
9. Add base models.
10. Add tenant model.
11. Add user, role, membership models.
12. Add auth stub.
13. Add RBAC dependency.
14. Add audit log model and helper.
15. Add catalog version model.
16. Add E-ITS module model.
17. Add E-ITS measure model.
18. Add module-measure relation.
19. Add catalog import service.
20. Add catalog API.
21. Add catalog UI.
22. Add business process model/API/UI.
23. Add asset model/API/UI.
24. Add asset relations.
25. Add protection need fields.
26. Add module mapping model/API/UI.
27. Add IMR generation service.
28. Add implementation plan API/UI.
29. Add risk register API/UI.
30. Add evidence upload/linking API/UI.

---

## 25. Prohibited Agent Behavior

Coding agents must not:

- rewrite the whole application without explicit request;
- introduce a new framework without approval;
- skip migrations for database changes;
- remove tests to make builds pass;
- ignore tenant isolation;
- implement authorization only in frontend;
- commit `.env` or secrets;
- create fake compliance logic that looks authoritative;
- overwrite existing user data in seed/import scripts;
- mutate activated catalog versions;
- generate large unrelated refactors during feature work.

---

## 26. Useful Local Commands

```bash
# Start infrastructure
docker compose up -d postgres redis minio

# Start all services
docker compose up --build

# Backend dev
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Frontend dev
cd frontend
pnpm dev

# Migrations
cd backend
alembic upgrade head
alembic revision --autogenerate -m "message"

# Tests
pytest
pnpm test
pnpm exec playwright test

# Quality
ruff check .
ruff format --check .
mypy app
pnpm lint
pnpm typecheck
```

---

## 27. Glossary

| Term | Meaning |
|---|---|
| E-ITS | Estonian Information Security Standard |
| ISMS | Information Security Management System |
| IMR | Information security measures implementation plan |
| Tenant | Organization using the system |
| Business process | Organizational process that needs protection |
| Asset | Information, system, service, component, location, or resource requiring protection |
| Target object | Object to which E-ITS modules and measures may apply |
| Protection need | Required level of confidentiality, integrity, and availability |
| Module | E-ITS baseline module |
| Measure | E-ITS security measure |
| Evidence | Document, file, URL, or record proving implementation |
| Audit log | Immutable change history |
| Risk treatment | Decision on how to handle a risk |

---

## 28. Language Policy

- Code identifiers: English.
- Database table and column names: English.
- API field names: English.
- Documentation: English by default.
- User-facing UI: initially English; later add Estonian i18n.
- E-ITS official terms may be stored in Estonian as display labels where required.

---

## 29. Final Instruction to Agents

When in doubt, do less but do it correctly.

For this project, a small secure and auditable feature is better than a large incomplete one.
