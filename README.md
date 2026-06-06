# E-ITS Management System

A web-based compliance management system for E-ITS (Estonian Information Security Standard). Manage organizations, users, business processes, assets, E-ITS catalog modules, implementation plans (IMR), risks, and evidence with full audit trails.

## Tech Stack


| Layer | Technology |
|---|---|
| Frontend | React 18 + TypeScript, Vite, Tailwind CSS, Radix UI, Vitest |
| Backend | Python 3.11 + FastAPI, SQLAlchemy 2.0, Alembic, Pydantic |
| Database | PostgreSQL 16 |
| Cache/Queue | Redis 7 |
| Object Storage | MinIO (S3-compatible) |
| Orchestration | Docker Compose |
| Linting | Ruff (backend), ESLint + Prettier (frontend) |

## Prerequisites

- Docker & Docker Compose
- Python 3.11+
- Node.js 20+ (LTS)
- [pnpm](https://pnpm.io/installation)
- Make

## Quick Start

```bash
# 1. Clone and enter the project
git clone <repo-url>
cd eits_cyberplan

# 2. Copy environment variables
cp .env.example .env

# 3. Start infrastructure services
docker compose up -d postgres redis minio

# 4. Install dependencies and seed database
make setup
make migrate
make seed

# 5. Start development servers
make dev
```

Frontend opens at **http://localhost:5173**, backend API at **http://localhost:8000**. OpenAPI docs are at **http://localhost:8000/docs**.

## Service Ports

| Service | URL |
|---|---|
| Frontend | http://localhost:5173 |
| Backend API | http://localhost:8000 |
| OpenAPI docs | http://localhost:8000/docs |
| PostgreSQL | localhost:5432 |
| Redis | localhost:6379 |
| MinIO console | http://localhost:9001 |

## Make Targets

```bash
make help          # Show all available targets
make setup        # Install dependencies and prepare .env
make dev         # Start backend and frontend in dev mode
make migrate     # Apply database migrations
make migration   # Create a migration (MESSAGE="...")
make seed       # Seed demo data
make test        # Run all tests
make test-backend  # Backend tests only (pytest)
make test-frontend # Frontend tests only (vitest)
make lint        # Run linters
make format      # Format code
make typecheck  # Run type checkers
make quality    # lint + format check + typecheck + tests
make down      # Stop all Docker Compose services
make clean      # Remove generated files
```

## Running Tests

```bash
# All tests
make test

# Backend only
make test-backend

# Frontend only
make test-frontend

# Full quality check (lint + typecheck + tests)
make quality
```

## Managing Docker Services

```bash
# Restart all services (backend + frontend)
docker compose restart backend frontend

# Restart only backend
docker compose restart backend

# Restart only frontend
docker compose restart frontend

# Stop all services
docker compose stop

# Start all services
docker compose start

# View logs
docker compose logs -f backend
docker compose logs -f frontend

# Full restart (stop + start)
docker compose stop backend frontend && docker compose start backend frontend
```

## Pre-Live Deployment

See [deploy/README.md](deploy/README.md) for the full deployment guide.

### Quick Deploy (Ubuntu VPS)

```bash
# SSH into your VPS, then:
bash <(curl -sL https://raw.githubusercontent.com/asiaat/eits_cyberplan/main/deploy/deploy.sh)
```

Or from a local clone:

```bash
make deploy
```

The script installs Docker, clones the repo, generates secrets, builds images, runs migrations, and seeds demo data.

### Make Targets for Production

```bash
make prod-build   # Build production Docker images
make prod-up      # Start production stack (nginx on :5071)
make prod-logs    # Tail production logs
make prod-down    # Stop production stack
make deploy       # Run full deploy script (idempotent)
```

### Manual Production Commands

```bash
# Start with custom port
HTTP_PORT=5071 docker compose -f deploy/docker-compose.yml up -d --build

# Run migrations
docker compose -f deploy/docker-compose.yml exec backend alembic upgrade head

# Seed demo data
docker compose -f deploy/docker-compose.yml exec backend python -m app.db.init_db

# Stop
docker compose -f deploy/docker-compose.yml down
```

### Architecture (Production)

```
Browser ──► nginx (:5071)
               ├── / ───────────► static frontend files (built SPA)
               ├── /api/v2/* ───► backend:8000
               └── /docs       ─► backend:8000
```

## Project Structure

```
eits_cyberplan/
├── backend/
│   ├── app/              # FastAPI application
│   │   ├── api/v1/       # API route handlers
│   │   ├── models/       # SQLAlchemy models
│   │   ├── schemas/      # Pydantic request/response schemas
│   │   ├── services/    # Business logic
│   │   ├── repositories/ # Database access layer
│   │   └── importers/   # E-ITS catalog importers
│   ├── alembic/versions/ # Database migrations
│   └── tests/         # Backend tests
├── frontend/
│   ├── src/
│   │   ├── pages/     # Page components
│   │   ├── components/ # Shared UI components
│   │   ├── features/  # Feature modules
│   │   ├── lib/      # API client, auth helpers
│   │   ├── hooks/    # React hooks
│   │   └── types/    # TypeScript types
│   └── tests/        # Frontend tests
├── infra/docker/      # Dockerfiles
├── docs/             # Architecture and SOP docs
├── docker-compose.yml # Service definitions
└── Makefile          # Development tasks
```

## Environment Variables

Copy `.env.example` to `.env` and adjust values for your local environment. Key variables:

- `DATABASE_URL` — PostgreSQL connection string
- `REDIS_URL` — Redis connection string
- `MINIO_*` — MinIO object storage settings
- `JWT_SECRET_KEY` — JWT signing key (change in production)
- `BACKEND_CORS_ORIGINS` — Allowed frontend origins

## Common Issues

**Database connection refused** — Ensure the postgres container is running:
```bash
docker compose ps
docker compose logs postgres
```

**Backend import errors** — Make sure the virtualenv is activated:
```bash
source backend/.venv/bin/activate
```

**Frontend not loading** — Check that the backend API is reachable at localhost:8000. The frontend expects `VITE_API_URL` to point to the backend.

## Contributing

See [AGENT.md](AGENT.md) for development conventions, coding directives, SOPs, and agent usage guidelines.