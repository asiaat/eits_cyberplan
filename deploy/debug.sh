#!/usr/bin/env bash
# E-ITS CyberPlan - Debug Script
# Run this on the VPS to diagnose deployment issues

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

info()  { echo -e "${GREEN}[INFO]${NC}  $1"; }
warn()  { echo -e "${YELLOW}[WARN]${NC}  $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; }

COMPOSE_FILE="deploy/docker-compose.yml"
APP_DIR="${APP_DIR:-/opt/eits}"
ENV_FILE="$APP_DIR/.env"

run_compose() {
    local cmd="$1"
    shift
    if [ -n "$PROJECT_NAME" ]; then
        docker compose -p "$PROJECT_NAME" --env-file "$ENV_FILE" -f "$COMPOSE_FILE" "$cmd" "$@" 2>&1
    else
        docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" "$cmd" "$@" 2>&1
    fi
}

echo "========================================"
echo "  E-ITS CyberPlan - Deployment Debug"
echo "========================================"
echo ""

# Detect project name
echo "=== Detecting Project Name ==="
PROJECT_NAME=""
for name in "eits" ""; do
    if [ -n "$name" ]; then
        if docker compose -p "$name" --env-file "$ENV_FILE" -f "$COMPOSE_FILE" ps &>/dev/null 2>&1; then
            PROJECT_NAME="$name"
            info "Found project name: '$name'"
            break
        fi
    else
        if docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" ps &>/dev/null 2>&1; then
            PROJECT_NAME=""
            info "Using default project name (empty)"
            break
        fi
    fi
done
echo ""

# 1. Port check
echo "=== Port Check ==="
if ss -tlnp 2>/dev/null | grep -q 5071; then
    info "Port 5071 is LISTENING"
    ss -tlnp | grep 5071
elif netstat -tlnp 2>/dev/null | grep -q 5071; then
    info "Port 5071 is LISTENING"
    netstat -tlnp | grep 5071
else
    error "Port 5071 is NOT listening!"
fi
echo ""

# 2. Container status
echo "=== Container Status ==="
docker ps -a --format "table {{.Names}}\t{{.Status}}\t{{.Image}}" 2>&1 | grep -E "eits|nginx|backend|postgres|redis|minio" || echo "(no eits containers found)"
echo ""

# 3. All docker containers
echo "=== All Docker Containers ==="
docker ps -a --format "table {{.Names}}\t{{.Status}}\t{{.Image}}" 2>&1 | head -20
echo ""

# 4. Nginx logs
echo "=== Nginx Logs (last 20 lines) ==="
run_compose logs nginx --tail=20 || true
echo ""

# 5. Backend logs
echo "=== Backend Logs (last 20 lines) ==="
run_compose logs backend --tail=20 || true
echo ""

# 6. Nginx config check
echo "=== Nginx Config Test ==="
run_compose exec nginx nginx -t 2>&1 || true
echo ""

# 7. Backend health from inside container
echo "=== Backend Health (from container) ==="
run_compose exec -T backend curl -s --max-time 5 http://localhost:8000/health 2>&1 || true
echo ""

# 8. Nginx config inside container
echo "=== Nginx Config (inside container) ==="
run_compose exec nginx cat /etc/nginx/conf.d/default.conf 2>&1 | head -40 || true
echo ""

# 9. Can nginx reach backend?
echo "=== Nginx -> Backend Connectivity ==="
run_compose exec nginx wget -qO- --timeout=5 http://backend:8000/health 2>&1 || true
echo ""

# 10. Docker networks
echo "=== Docker Networks ==="
docker network ls 2>&1 | grep -E "eits|NETWORK" || true
echo ""

# 11. Docker volumes
echo "=== Docker Volumes ==="
docker volume ls 2>&1 | grep -E "eits|VOLUME" || true
echo ""

# 12. Quick fix suggestions
echo "========================================"
echo "  Quick Fixes"
echo "========================================"
echo ""
echo "If containers exist but show no status:"
echo "  docker ps -a | grep eits"
echo ""
echo "If nginx is not running:"
echo "  run_compose restart nginx"
echo ""
echo "If backend is not running:"
echo "  run_compose restart backend"
echo ""
echo "If port not open in firewall (Hostinger hPanel):"
echo "  VPS → Firewalls → Add rule: TCP 5071 → Accept"
echo ""
echo "Full redeploy:"
echo "  cd $APP_DIR && git pull && bash deploy/deploy.sh"
echo ""
echo "Remove stuck containers and redeploy:"
echo "  docker rm -f \$(docker ps -aq) 2>/dev/null; docker volume rm -f \$(docker volume ls -q) 2>/dev/null; bash deploy/deploy.sh"
echo ""