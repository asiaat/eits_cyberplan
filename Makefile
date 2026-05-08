.PHONY: help setup dev backend-install frontend-install migrate migration seed test test-backend test-frontend lint format typecheck quality openapi down clean

help:
	@echo "E-ITS Management System - Makefile"
	@echo ""
	@echo "Available targets:"
	@echo "  setup              - Install dependencies and prepare local env"
	@echo "  dev                - Run backend and frontend in dev mode"
	@echo "  backend-install    - Install Python dependencies"
	@echo "  frontend-install   - Install Node dependencies"
	@echo "  migrate            - Apply Alembic migrations"
	@echo "  migration          - Create a new Alembic migration (MESSAGE=...)"
	@echo "  seed               - Seed demo data"
	@echo "  test               - Run all tests"
	@echo "  test-backend       - Run backend tests"
	@echo "  test-frontend     - Run frontend tests"
	@echo "  lint               - Run linters"
	@echo "  format             - Format code"
	@echo "  typecheck          - Run type checkers"
	@echo "  quality            - Run lint, format check, typecheck, and tests"
	@echo "  openapi            - Export OpenAPI JSON"
	@echo "  down               - Stop all services"
	@echo "  clean              - Remove generated files"

setup: backend-install frontend-install
	@cp -n .env.example .env 2>/dev/null || true
	@echo "Environment ready. Edit .env if needed."

dev:
	@mkdir -p logs
	@echo "Starting backend (logs/backend.log)..."
	@cd backend && . .venv/bin/activate && PYTHONPATH=. uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 >> ../logs/backend.log 2>&1 &
	@echo "Starting frontend (logs/frontend.log)..."
	@cd frontend && pnpm dev >> ../logs/frontend.log 2>&1 &

backend-install:
	@cd backend && python3 -m venv .venv && \
	. .venv/bin/activate && \
	python -m pip install --upgrade pip && \
	ruff check . || true && \
	uv sync

frontend-install:
	cd frontend && pnpm install

migrate:
	cd backend && . .venv/bin/activate && PYTHONPATH=. alembic upgrade head

migration:
	cd backend && . .venv/bin/activate && PYTHONPATH=. alembic revision --autogenerate -m "$(MESSAGE)"

seed:
	cd backend && . .venv/bin/activate && PYTHONPATH=. python -m app.db.init_db

test: test-backend test-frontend

test-backend:
	cd backend && . .venv/bin/activate && PYTHONPATH=. pytest -v

test-frontend:
	cd frontend && pnpm test

lint:
	cd backend && . .venv/bin/activate && ruff check .
	cd frontend && pnpm lint

format:
	cd backend && . .venv/bin/activate && ruff format .
	cd frontend && pnpm format

typecheck:
	cd backend && . .venv/bin/activate && mypy app
	cd frontend && pnpm typecheck

quality: lint format typecheck test

openapi:
	cd backend && . .venv/bin/activate && python scripts/export_openapi.py

down:
	docker compose down

clean:
	rm -rf .venv __pycache__ backend/__pycache__ backend/app/__pycache__
	rm -rf node_modules frontend/node_modules
	rm -rf dist frontend/dist
	rm -rf .pytest_cache
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true