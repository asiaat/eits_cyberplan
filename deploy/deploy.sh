#!/usr/bin/env bash
# ==============================================================
# E-ITS CyberPlan - Pre-Live Deployment Script
# Run this ON the VPS as root (or with sudo).
#
# Usage:
#   bash deploy/deploy.sh
#
# Environment variables (optional overrides):
#   REPO_URL    - Git repository URL (default: GitHub)
#   APP_DIR     - Deployment directory (default: /opt/eits)
#   HTTP_PORT   - HTTP port (default: 5071)
#   HTTPS_PORT  - HTTPS port (default: 5471)
# ==============================================================

set -euo pipefail

REPO_URL="${REPO_URL:-https://github.com/asiaat/eits_cyberplan.git}"
APP_DIR="${APP_DIR:-/opt/eits}"
HTTP_PORT="${HTTP_PORT:-5071}"
HTTPS_PORT="${HTTPS_PORT:-5471}"
COMPOSE_FILE="deploy/docker-compose.yml"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

info()  { echo -e "${GREEN}[INFO]${NC}  $1"; }
warn()  { echo -e "${YELLOW}[WARN]${NC}  $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }

# ------------------------------------------------------------------
# 1. Prerequisites
# ------------------------------------------------------------------
info "Checking prerequisites..."

if [ "$(id -u)" -ne 0 ]; then
    error "This script must be run as root (or with sudo)."
fi

if ! command -v docker &>/dev/null; then
    info "Installing Docker..."
    apt-get update -qq
    apt-get install -y -qq docker.io docker-compose-plugin
    systemctl enable --now docker
    info "Docker installed."
else
    info "Docker already installed."
fi

# ------------------------------------------------------------------
# 2. Clone / update repository
# ------------------------------------------------------------------
if [ -d "$APP_DIR" ]; then
    info "Updating repository at $APP_DIR..."
    cd "$APP_DIR"
    git pull
else
    info "Cloning repository into $APP_DIR..."
    git clone "$REPO_URL" "$APP_DIR"
    cd "$APP_DIR"
fi

# Strip stale deploy/.env that would interfere with .env loading
rm -f deploy/.env

# ------------------------------------------------------------------
# 3. Detect VPS IP
# ------------------------------------------------------------------
VPS_IP=""
if command -v curl &>/dev/null; then
    VPS_IP=$(curl -s --max-time 5 http://checkip.amazonaws.com 2>/dev/null || \
             curl -s --max-time 5 https://api.ipify.org 2>/dev/null || true)
fi
if [ -z "$VPS_IP" ]; then
    VPS_IP="<your-server-ip>"
    warn "Could not detect public IP. Set BACKEND_CORS_ORIGINS manually."
fi

# ------------------------------------------------------------------
# 4. Generate .env at repo root
# ------------------------------------------------------------------
if [ -f .env ] && grep -q "change-me" .env 2>/dev/null; then
    warn ".env exists but contains placeholder values — regenerating."
    rm -f .env
fi

if [ ! -f .env ]; then
    info "Generating .env with random secrets..."

    POSTGRES_PASSWORD=$(openssl rand -hex 32)
    JWT_SECRET_KEY=$(openssl rand -hex 32)
    MINIO_ACCESS_KEY=$(openssl rand -hex 16)
    MINIO_SECRET_KEY=$(openssl rand -hex 32)

    cat > .env <<EOF
APP_ENV=staging
APP_NAME=eits-cyberplan

POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_DB=eits
POSTGRES_USER=eits
POSTGRES_PASSWORD=${POSTGRES_PASSWORD}

DATABASE_URL=postgresql+psycopg://eits:${POSTGRES_PASSWORD}@postgres:5432/eits

REDIS_URL=redis://redis:6379/0

MINIO_ENDPOINT=minio:9000
MINIO_PUBLIC_ENDPOINT=${VPS_IP}:9000
MINIO_ACCESS_KEY=${MINIO_ACCESS_KEY}
MINIO_SECRET_KEY=${MINIO_SECRET_KEY}
MINIO_BUCKET=eits-evidence
MINIO_SECURE=false

JWT_SECRET_KEY=${JWT_SECRET_KEY}
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=480

VITE_API_URL=/api/v2

BACKEND_CORS_ORIGINS=http://${VPS_IP}:${HTTP_PORT}

LOG_LEVEL=INFO
EOF

    info ".env generated."
else
    info ".env already exists with custom values — keeping it."
fi

# Compose options: always use --env-file for deterministic .env loading
COMPOSE_OPTS="--env-file $APP_DIR/.env -f $COMPOSE_FILE --project-directory $APP_DIR"

# ------------------------------------------------------------------
# 5. Remove old containers, build and start fresh
# ------------------------------------------------------------------
info "Removing old containers..."
for c in eits_postgres eits_redis eits_minio eits_backend eits_nginx; do
    docker rm -f "$c" 2>/dev/null || true
done
docker compose $COMPOSE_OPTS down --remove-orphans 2>/dev/null || true

info "Building and starting services (HTTP :$HTTP_PORT)..."
HTTP_PORT="$HTTP_PORT" HTTPS_PORT="$HTTPS_PORT" \
docker compose $COMPOSE_OPTS up -d --build

# ------------------------------------------------------------------
# 6. Wait for backend to become healthy (migrations + seed run in entrypoint)
# ------------------------------------------------------------------
health_check() {
    docker compose $COMPOSE_OPTS exec -T backend curl -s --max-time 2 http://localhost:8000/health &>/dev/null
}

info "Waiting for backend to be ready..."
for i in $(seq 1 60); do
    if health_check; then
        info "Backend is healthy."
        break
    fi
    if [ "$i" -eq 60 ]; then
        for c in eits_postgres eits_redis eits_minio eits_backend eits_nginx; do
            docker rm -f "$c" 2>/dev/null || true
        done
        warn "Checking for stale postgres password..."
        if docker volume inspect eits_postgres_data &>/dev/null && \
           docker logs eits_backend 2>&1 | grep -q "password authentication failed"; then
            warn "Postgres volume has a stale password. Wiping it and retrying..."
            docker volume rm -f eits_postgres_data 2>/dev/null || true
            HTTP_PORT="$HTTP_PORT" HTTPS_PORT="$HTTPS_PORT" \
            docker compose $COMPOSE_OPTS up -d
            for j in $(seq 1 60); do
                if health_check; then
                    info "Backend is healthy after volume reset."
                    break
                fi
                if [ "$j" -eq 60 ]; then
                    warn "Backend still unhealthy after volume reset — check logs: docker compose -f $COMPOSE_FILE logs backend"
                fi
                sleep 2
            done
        else
            warn "Backend health check timed out — check logs: docker compose -f $COMPOSE_FILE logs backend"
        fi
    fi
    sleep 2
done

# ------------------------------------------------------------------
# 7. Done
# ------------------------------------------------------------------
echo ""
echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}  Deployment Complete!${NC}"
echo -e "${GREEN}============================================${NC}"
echo ""
echo "  Access the application at:"
echo ""
echo -e "  ${GREEN}http://${VPS_IP}:${HTTP_PORT}${NC}"
echo ""
echo "  To view logs:"
echo "    docker compose --env-file .env -f deploy/docker-compose.yml logs -f"
echo ""
echo "  To stop:"
echo "    docker compose --env-file .env -f deploy/docker-compose.yml down"
echo ""

echo "  ┌─────────────────────────────────────────────────┐"
echo "  │  IMPORTANT: Save these credentials securely!    │"
echo "  │  They will not be shown again.                  │"
echo "  └─────────────────────────────────────────────────┘"
echo ""
echo "  PostgreSQL password:  ${POSTGRES_PASSWORD:-<existing>}"
echo "  JWT secret key:       ${JWT_SECRET_KEY:-<existing>}"
echo "  MinIO access key:     ${MINIO_ACCESS_KEY:-<existing>}"
echo "  MinIO secret key:     ${MINIO_SECRET_KEY:-<existing>}"
echo ""
