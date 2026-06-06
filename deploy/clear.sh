#!/usr/bin/env bash
# ==============================================================
# E-ITS CyberPlan - Teardown Script
# Removes all containers and compose resources (preserves data).
# 
# Usage:
#   bash deploy/clear.sh                     # remove containers + networks only
#   bash deploy/clear.sh --volumes           # also delete all data volumes
#   bash deploy/clear.sh -v                  # same as --volumes
# ==============================================================

set -euo pipefail

APP_DIR="$(cd "$(dirname "$0")/.." && pwd)"
COMPOSE_FILE="deploy/docker-compose.yml"
COMPOSE_OPTS="--env-file $APP_DIR/.env -f $COMPOSE_FILE --project-directory $APP_DIR"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

info()  { echo -e "${GREEN}[INFO]${NC}  $1"; }
warn()  { echo -e "${YELLOW}[WARN]${NC}  $1"; }

info "Stopping and removing all eits containers..."
for c in eits_postgres eits_redis eits_minio eits_backend eits_nginx; do
    docker rm -f "$c" 2>/dev/null || true
done

info "Removing compose networks and resources..."
docker compose $COMPOSE_OPTS down --remove-orphans 2>/dev/null || true

if [ "${1:-}" = "--volumes" ] || [ "${1:-}" = "-v" ]; then
    info "Removing all data volumes..."
    docker volume rm -f eits_postgres_data eits_redis_data eits_minio_data 2>/dev/null || true
    info "All data volumes removed."
else
    echo ""
    echo "  Data volumes preserved. To also delete all data, re-run with --volumes:"
    echo "    bash deploy/clear.sh --volumes"
    echo ""
    echo "  Individual volume names if you want to be selective:"
    echo "    eits_postgres_data   — PostgreSQL database"
    echo "    eits_redis_data      — Redis cache"
    echo "    eits_minio_data      — MinIO evidence files"
fi

info "Done."
