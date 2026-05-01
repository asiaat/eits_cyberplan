# SOP: Local Development

## Prerequisites

- Docker & Docker Compose
- Python 3.11+
- Node.js LTS (20+)
- pnpm

## Initial Setup

```bash
# 1. Clone repository
git clone <repo-url>
cd eits_cyberplan

# 2. Copy environment file
cp .env.example .env

# 3. Start infrastructure
docker compose up -d postgres redis minio

# 4. Install backend deps
cd backend && python -m venv .venv && source .venv/bin/activate && pip install -e ".[dev]"

# 5. Install frontend deps
cd ../frontend && pnpm install

# 6. Run migrations
cd ../backend && alembic upgrade head

# 7. Seed data
python -m app.db.init_db

# 8. Start development
make dev  # or: uvicorn app.main:app --reload & cd ../frontend && pnpm dev
```

## Ports

- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- OpenAPI docs: http://localhost:8000/docs
- PostgreSQL: localhost:5432
- MinIO console: http://localhost:9001

## Running Tests

```bash
make test-backend
make test-frontend
make quality
```

## Common Issues

### Database connection refused
- Ensure postgres container is running: `docker compose ps`
- Check `.env` values match docker-compose.yml

### Import errors in backend
- Ensure virtualenv is activated: `source .venv/bin/activate`
- Reinstall deps: `pip install -e ".[dev]"`