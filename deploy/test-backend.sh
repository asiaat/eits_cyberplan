#!/usr/bin/env bash
# E-ITS CyberPlan - Backend Test Script
# Run on VPS: cd /opt/eits && bash deploy/test-backend.sh

set -euo pipefail

PROJECT_NAME="${PROJECT_NAME:-eits}"
APP_DIR="${APP_DIR:-/opt/eits}"
COMPOSE_FILE="$APP_DIR/deploy/docker-compose.yml"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

info()  { echo -e "${GREEN}[INFO]${NC}  $1"; }
warn()  { echo -e "${YELLOW}[WARN]${NC}  $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }

echo "========================================"
echo "  E-ITS CyberPlan - Backend Tests"
echo "========================================"
echo ""

# 1. Rebuild backend with dev dependencies (includes pytest)
info "Rebuilding backend with test dependencies..."
docker compose -p "$PROJECT_NAME" --env-file "$APP_DIR/.env" -f "$COMPOSE_FILE" build backend

# 2. Start backend if not running
info "Ensuring backend is running..."
docker compose -p "$PROJECT_NAME" --env-file "$APP_DIR/.env" -f "$COMPOSE_FILE" up -d backend

# 3. Wait for backend to be healthy
info "Waiting for backend to be healthy..."
for i in $(seq 1 30); do
    if docker compose -p "$PROJECT_NAME" --env-file "$APP_DIR/.env" -f "$COMPOSE_FILE" exec -T backend curl -s --max-time 2 http://localhost:8000/health &>/dev/null; then
        info "Backend is healthy."
        break
    fi
    if [ "$i" -eq 30 ]; then
        error "Backend did not become healthy. Check logs: docker compose -p $PROJECT_NAME --env-file .env -f deploy/docker-compose.yml logs backend"
    fi
    sleep 2
done

# 4. Run pytest
echo ""
info "Running pytest..."
echo ""

docker compose -p "$PROJECT_NAME" --env-file "$APP_DIR/.env" -f "$COMPOSE_FILE" exec -T backend /app/backend/.venv/bin/python -m pytest /app/backend/backend/tests/ -v --tb=short 2>&1 || true

echo ""
echo "========================================"
echo "  Tests Complete"
echo "========================================"