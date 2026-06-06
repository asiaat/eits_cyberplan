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

echo "========================================"
echo "  E-ITS CyberPlan - Deployment Debug"
echo "========================================"
echo ""

# 1. Port check
echo "=== Port Check ==="
if ss -tlnp 2>/dev/null | grep -q 5071; then
    info "Port 5071 is LISTENING"
    ss -tlnp | grep 5071
else
    error "Port 5071 is NOT listening!"
    ss -tlnp | grep -E "5071|nginx" || true
fi
echo ""

# 2. Container status
echo "=== Container Status ==="
docker compose --env-file .env -f "$COMPOSE_FILE" ps
echo ""

# 3. Nginx logs
echo "=== Nginx Logs (last 20 lines) ==="
docker compose --env-file .env -f "$COMPOSE_FILE" logs nginx --tail=20 2>&1 || true
echo ""

# 4. Backend logs
echo "=== Backend Logs (last 20 lines) ==="
docker compose --env-file .env -f "$COMPOSE_FILE" logs backend --tail=20 2>&1 || true
echo ""

# 5. Nginx config check
echo "=== Nginx Config Test ==="
docker compose --env-file .env -f "$COMPOSE_FILE" exec nginx nginx -t 2>&1 || true
echo ""

# 6. Backend health from inside container
echo "=== Backend Health (from container) ==="
docker compose --env-file .env -f "$COMPOSE_FILE" exec -T backend curl -s --max-time 5 http://localhost:8000/health 2>&1 || true
echo ""

# 7. Nginx config inside container
echo "=== Nginx Config (inside container) ==="
docker compose --env-file .env -f "$COMPOSE_FILE" exec nginx cat /etc/nginx/conf.d/default.conf 2>&1 | head -40 || true
echo ""

# 8. Can nginx reach backend?
echo "=== Nginx -> Backend Connectivity ==="
docker compose --env-file .env -f "$COMPOSE_FILE" exec nginx wget -qO- --timeout=5 http://backend:8000/health 2>&1 || true
echo ""

# 9. Docker network
echo "=== Docker Networks ==="
docker network ls | grep eits || true
echo ""

# 10. Quick fix suggestions
echo "========================================"
echo "  Quick Fixes"
echo "========================================"
echo ""
echo "If nginx is not running:"
echo "  docker compose -f $COMPOSE_FILE restart nginx"
echo ""
echo "If backend is not running:"
echo "  docker compose -f $COMPOSE_FILE restart backend"
echo ""
echo "If port not open in firewall (Hostinger hPanel):"
echo "  VPS → Firewalls → Add rule: TCP 5071 → Accept"
echo ""
echo "Full redeploy:"
echo "  cd $APP_DIR && git pull && bash deploy/deploy.sh"
echo ""