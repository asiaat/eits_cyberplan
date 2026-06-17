# Operations — E-ITS Management System

Runbook for maintaining, monitoring, and tuning the E-ITS Management System in pre-live and production environments.

---

## 1. Environment Variables Reference

All env vars are defined in `backend/app/core/config.py` (Pydantic `Settings` class). The backend loads them from the repo-root `.env` file.

### 1.1 Application

| Variable | Default | Prod Required | Description |
|---|---|---|---|
| `APP_ENV` | `local` | Yes | Runtime environment: `local`, `staging`, `production` |
| `APP_NAME` | `eits-management-system` | No | Application name used in health check responses |
| `LOG_LEVEL` | `INFO` | No | Python logging level: `DEBUG`, `INFO`, `WARNING`, `ERROR` |

### 1.2 PostgreSQL

| Variable | Default | Prod Required | Description |
|---|---|---|---|
| `POSTGRES_HOST` | `localhost` | Yes | PostgreSQL hostname (service name in Docker) |
| `POSTGRES_PORT` | `5432` | No | PostgreSQL port |
| `POSTGRES_DB` | `eits` | No | Database name |
| `POSTGRES_USER` | `eits` | No | Database user |
| `POSTGRES_PASSWORD` | `eits_dev_password` | **Yes** | Database password (use a random 64-char hex in production) |
| `DATABASE_URL` | auto-built from individual vars | No | Full connection string; overrides individual `POSTGRES_*` vars if set |

The `DATABASE_URL` is assembled from individual components when not explicitly set. In production, you may set it directly for simplicity.

### 1.3 Redis

| Variable | Default | Prod Required | Description |
|---|---|---|---|
| `REDIS_URL` | `redis://redis:6379/0` | Yes | Redis connection string |

Redis is used for session caching and future background job queues.

### 1.4 MinIO (Object Storage)

| Variable | Default | Prod Required | Description |
|---|---|---|---|
| `MINIO_ENDPOINT` | `minio:9000` | Yes | Internal MinIO endpoint (service:port) |
| `MINIO_PUBLIC_ENDPOINT` | empty | No | External-accessible MinIO endpoint for browser uploads; set to `VPS_IP:9000` or your domain |
| `MINIO_ACCESS_KEY` | `minioadmin` | **Yes** | MinIO root username (use a random 32-char hex in production) |
| `MINIO_SECRET_KEY` | `minioadmin` | **Yes** | MinIO root password (use a random 64-char hex in production) |
| `MINIO_BUCKET` | `eits-evidence` | No | Default bucket for evidence file uploads |
| `MINIO_SECURE` | `false` | No | Use HTTPS for MinIO connections; set to `true` when TLS is configured |

### 1.5 Authentication

| Variable | Default | Prod Required | Description |
|---|---|---|---|
| `JWT_SECRET_KEY` | `change-me-in-local-only` | **Yes** | HMAC signing key for JWT tokens (use `openssl rand -hex 32` in production) |
| `JWT_ALGORITHM` | `HS256` | No | JWT signing algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `480` | No | Token lifetime in minutes (8 hours default; consider 60 for production) |

### 1.6 CORS

| Variable | Default | Prod Required | Description |
|---|---|---|---|
| `BACKEND_CORS_ORIGINS` | `http://localhost:5173,http://127.0.0.1:5173` | **Yes** | Comma-separated list of allowed frontend origins; must include the full public URL of your deployment |

### 1.7 Frontend

| Variable | Default | Prod Required | Description |
|---|---|---|---|
| `VITE_API_URL` | `/api/v2` | No | API base path for the frontend; uses a relative path in production to proxy through nginx |

### 1.8 E-ITS Catalog Import

| Variable | Default | Prod Required | Description |
|---|---|---|---|
| `EITS_IMPORT_YEAR` | `2024` | No | Target E-ITS catalog version year |
| `EITS_SOURCE_URL` | *(RIAA source URL)* | No | URL to fetch the official E-ITS catalog from |

---

## 2. Routine Maintenance

### 2.1 Log Rotation

Docker containers write to stdout/stderr, which Docker captures in JSON files. By default these grow unbounded.

```bash
# Check current log sizes
du -sh /var/lib/docker/containers/*/*-json.log

# Configure global log rotation (add to /etc/docker/daemon.json):
# {
#   "log-driver": "json-file",
#   "log-opts": {
#     "max-size": "10m",
#     "max-file": "3"
#   }
# }
# Then: systemctl restart docker
```

To apply rotation per-container without restarting Docker, add to the compose service:

```yaml
logging:
  driver: json-file
  options:
    max-size: "10m"
    max-file: "3"
```

### 2.2 Disk Space Monitoring

```bash
# Overall usage
df -h

# Docker disk usage
docker system df

# Clean up unused images, containers, and build cache
docker system prune -a --volumes

# Clean build cache only (safest — keeps images and containers)
docker builder prune
```

Recommended monthly:
```bash
docker system prune -f                     # remove dangling resources
docker builder prune -f                    # remove build cache
```

### 2.3 Database Maintenance

PostgreSQL does not require routine `VACUUM FULL` but benefits from periodic maintenance:

```bash
# Analyze query planner statistics (safe to run anytime)
docker compose -p eits --env-file .env -f deploy/docker-compose.yml exec postgres \
  psql -U eits -d eits -c "ANALYZE;"

# Check for bloated tables
docker compose -p eits --env-file .env -f deploy/docker-compose.yml exec postgres \
  psql -U eits -d eits -c "
SELECT schemaname, relname, n_live_tup, n_dead_tup, 
       round(n_dead_tup::numeric / GREATEST(n_live_tup, 1), 2) AS dead_ratio
FROM pg_stat_user_tables
WHERE n_dead_tup > 1000
ORDER BY dead_ratio DESC;"

# Vacuum heavily updated tables if dead_ratio > 0.2
docker compose -p eits --env-file .env -f deploy/docker-compose.yml exec postgres \
  psql -U eits -d eits -c "VACUUM (VERBOSE, ANALYZE) <table_name>;"
```

Autovacuum is enabled by default in PostgreSQL 16 and handles most cases. Manual intervention is rarely needed.

### 2.4 TLS Certificate Renewal

Let's Encrypt certificates expire every 90 days. See `deploy/README.md` for setup steps.

Test renewal and restart nginx:

```bash
certbot renew --dry-run
# If successful, the cron job (set up during TLS setup) handles auto-renewal.
# The nginx container must be restarted after cert renewal:
docker compose -p eits --env-file .env -f deploy/docker-compose.yml restart nginx
```

### 2.5 OS and Docker Updates

```bash
# Update system packages
apt update && apt upgrade -y

# Check for Docker engine updates
apt install --only-upgrade docker.io docker-compose-plugin

# Reboot if kernel was updated
reboot
# After reboot, all containers restart automatically (restart: unless-stopped)
```

### 2.6 Application Updates (Redeploy)

```bash
cd /opt/eits
git pull
bash deploy/deploy.sh
```

This is idempotent: it rebuilds images, restarts containers, runs migrations, and reseeds the admin user. Data volumes are preserved.

---

## 3. Performance Optimization

### 3.1 PostgreSQL Tuning

The default PostgreSQL config in the Docker image is conservative. For a production VPS with 4+ GB RAM, create `/opt/eits/postgres-custom.conf` and mount it:

```ini
# Shared buffers (25% of RAM, max 8 GB)
shared_buffers = 1GB

# Effective cache size (75% of RAM)
effective_cache_size = 3GB

# Work memory for sorts (per operation)
work_mem = 32MB

# Maintenance operations (VACUUM, CREATE INDEX)
maintenance_work_mem = 256MB

# Query planner
random_page_cost = 1.1      # SSD storage
effective_io_concurrency = 200

# Connections
max_connections = 100
```

Apply by adding to the postgres service in `deploy/docker-compose.yml`:

```yaml
volumes:
  - postgres_data:/var/lib/postgresql/data
  - /opt/eits/postgres-custom.conf:/etc/postgresql/postgresql.conf.d/custom.conf
```

Always benchmark after changes — every workload is different.

### 3.2 nginx Caching and Compression

Already configured in `deploy/nginx.conf`:

- **Gzip** enabled for JSON, JS, CSS, SVG (min 256 bytes)
- **Static assets** cached for 1 year with `immutable` flag
- **Security headers** set on all responses

To add API response caching for read-heavy endpoints:

```nginx
location /api/v2/catalog/ {
    proxy_pass http://backend:8000;
    proxy_cache eits_cache;
    proxy_cache_valid 200 5m;
    proxy_cache_use_stale error timeout;
}
```

### 3.3 Redis Memory

Set a max memory policy to prevent Redis from consuming all server RAM:

```yaml
# In deploy/docker-compose.yml, add to redis service:
command: redis-server --maxmemory 256mb --maxmemory-policy allkeys-lru
```

### 3.4 Application-Level Optimization

- **N+1 queries**: The backend uses SQLAlchemy 2.0 with eager loading (`selectinload`) on detail endpoints. Monitor query logs for unexpected lazy loads.
- **Connection pooling**: SQLAlchemy's pool size defaults to 5; for production increase in `backend/app/db/session.py`:

```python
engine = create_async_engine(
    settings.database_url,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
)
```

- **Frontend bundle**: Vite's production build already treeshakes and minifies. Monitor bundle size with `pnpm build && pnpm preview`.

---

## 4. Monitoring & Health

### 4.1 Health Endpoints

| Endpoint | Method | Response |
|---|---|---|
| `/health` | GET | `{"status": "healthy", "app": "eits-cyberplan"}` |
| `/api/v2/health` | GET | Same (proxied through nginx) |

The health endpoint is unauthenticated. Use it for load balancer checks and monitoring.

### 4.2 Container Status

```bash
# Quick status check
docker compose -p eits --env-file .env -f deploy/docker-compose.yml ps

# All containers should show "Up" or "Up (healthy)"
# Expected output:
# eits_postgres   Up (healthy)
# eits_redis      Up (healthy)
# eits_minio      Up (healthy)
# eits_backend    Up
# eits_nginx      Up
```

### 4.3 Logs

```bash
# Tail all services
docker compose -p eits --env-file .env -f deploy/docker-compose.yml logs -f

# Tail a single service
docker compose -p eits --env-file .env -f deploy/docker-compose.yml logs -f backend

# Last N lines
docker compose -p eits --env-file .env -f deploy/docker-compose.yml logs --tail=100 backend

# Filter by log level
docker compose -p eits --env-file .env -f deploy/docker-compose.yml logs backend | grep ERROR
```

### 4.4 Log Levels

Change the log level at runtime by updating `.env` and restarting the backend:

```bash
# Temporarily enable debug logging
sed -i 's/LOG_LEVEL=INFO/LOG_LEVEL=DEBUG/' /opt/eits/.env
docker compose -p eits --env-file .env -f deploy/docker-compose.yml restart backend

# After debugging, restore
sed -i 's/LOG_LEVEL=DEBUG/LOG_LEVEL=INFO/' /opt/eits/.env
docker compose -p eits --env-file .env -f deploy/docker-compose.yml restart backend
```

### 4.5 Basic Alerting (No External Service)

A simple cron job to check health and send a notification:

```bash
#!/bin/bash
# /opt/eits/scripts/health-check.sh
HEALTH=$(curl -s --max-time 5 http://localhost:5071/health 2>/dev/null)
if ! echo "$HEALTH" | grep -q "healthy"; then
    echo "[$(date)] Backend unhealthy — response: $HEALTH" >> /var/log/eits-health.log
    # Optional: send email via mailutils or integrate with your monitoring
fi
```

```bash
# Add to crontab (every 5 minutes)
*/5 * * * * /opt/eits/scripts/health-check.sh
```

---

## 5. Backup & Restore

### 5.1 Database Backup

```bash
# One-off backup
BACKUP_DIR=/opt/eits/backups
mkdir -p "$BACKUP_DIR"
docker compose -p eits --env-file .env -f deploy/docker-compose.yml exec -T postgres \
  pg_dump -U eits eits > "$BACKUP_DIR/eits_$(date +%Y%m%d_%H%M%S).sql"

# Compress
gzip "$BACKUP_DIR/eits_$(date +%Y%m%d_%H%M%S).sql"
```

### 5.2 Automated Daily Backup

Add to the root crontab (`crontab -e`):

```cron
0 2 * * * cd /opt/eits && mkdir -p backups && docker compose -p eits --env-file .env -f deploy/docker-compose.yml exec -T postgres pg_dump -U eits eits | gzip > backups/eits_$(date +\%Y\%m\%d).sql.gz && find backups -name "eits_*.sql.gz" -mtime +30 -delete
```

This runs at 02:00 daily, keeps 30 days of backups, and prunes older ones.

### 5.3 MinIO (Evidence) Backup

```bash
# Backup the MinIO volume
docker run --rm -v eits_minio_data:/source -v /opt/eits/backups:/backup alpine \
  tar czf /backup/minio_$(date +%Y%m%d).tar.gz -C /source .
```

### 5.4 Database Restore

```bash
# Restore from a SQL dump
cat /opt/eits/backups/eits_20250101_020000.sql | \
  docker compose -p eits --env-file .env -f deploy/docker-compose.yml exec -T postgres \
  psql -U eits eits
```

From a compressed backup:
```bash
gunzip -c /opt/eits/backups/eits_20250101.sql.gz | \
  docker compose -p eits --env-file .env -f deploy/docker-compose.yml exec -T postgres \
  psql -U eits eits
```

**Important**: Stop the backend before restoring to prevent write conflicts during restore:

```bash
docker compose -p eits --env-file .env -f deploy/docker-compose.yml stop backend
# ... restore ...
docker compose -p eits --env-file .env -f deploy/docker-compose.yml start backend
```

### 5.5 Restore Test Checklist

Test at least monthly:

- [ ] Restore database to a test environment
- [ ] Restore MinIO evidence bucket
- [ ] Start the application
- [ ] Verify sample tenant data is accessible
- [ ] Verify evidence file download
- [ ] Document the result

---

## 6. Secret Rotation

### 6.1 PostgreSQL Password

```bash
# 1. Generate new password
NEW_PASS=$(openssl rand -hex 32)

# 2. Update .env
sed -i "s/^POSTGRES_PASSWORD=.*/POSTGRES_PASSWORD=$NEW_PASS/" /opt/eits/.env
sed -i "s;^DATABASE_URL=.*;DATABASE_URL=postgresql+psycopg://eits:$NEW_PASS@postgres:5432/eits;" /opt/eits/.env

# 3. Reset the PostgreSQL password (requires manual step inside the container)
docker compose -p eits --env-file .env -f deploy/docker-compose.yml exec postgres \
  psql -U eits -c "ALTER USER eits WITH PASSWORD '$NEW_PASS';"

# 4. Restart backend (picks up new .env)
docker compose -p eits --env-file .env -f deploy/docker-compose.yml restart backend
```

**Caution**: If the password is changed while the postgres data volume exists with the old password, the deploy script's stale-password recovery logic kicks in and wipes the volume. Always update the database password inside PostgreSQL first (step 3), then update `.env` and restart.

### 6.2 JWT Secret Key

```bash
# 1. Generate new key
NEW_JWT=$(openssl rand -hex 32)

# 2. Update .env
sed -i "s/^JWT_SECRET_KEY=.*/JWT_SECRET_KEY=$NEW_JWT/" /opt/eits/.env

# 3. Restart backend
docker compose -p eits --env-file .env -f deploy/docker-compose.yml restart backend
```

This invalidates all existing JWT tokens. All users must log in again.

### 6.3 MinIO Credentials

```bash
# 1. Generate new keys
NEW_ACCESS_KEY=$(openssl rand -hex 16)
NEW_SECRET_KEY=$(openssl rand -hex 32)

# 2. Update .env
sed -i "s/^MINIO_ACCESS_KEY=.*/MINIO_ACCESS_KEY=$NEW_ACCESS_KEY/" /opt/eits/.env
sed -i "s/^MINIO_SECRET_KEY=.*/MINIO_SECRET_KEY=$NEW_SECRET_KEY/" /opt/eits/.env

# 3. Update MinIO (via mc client or console) before restarting
docker compose -p eits --env-file .env -f deploy/docker-compose.yml exec minio \
  mc admin user info minio

# 4. Restart backend + minio
docker compose -p eits --env-file .env -f deploy/docker-compose.yml restart backend minio
```

---

## 7. Security Maintenance

### 7.1 Dependency Updates

Check for known vulnerabilities:

```bash
# Backend Python dependencies
cd /opt/eits/backend
source .venv/bin/activate
pip-audit               # if installed, or:
pip list --outdated

# Check for known vulnerabilities with pip-audit
pip install pip-audit && pip-audit
```

For the frontend:

```bash
cd /opt/eits/frontend
pnpm audit              # review advisory output
pnpm outdated           # see which packages are behind
```

Perform dependency updates monthly. For critical CVEs, patch immediately and redeploy.

### 7.2 Audit Log Review

The `audit_logs` table records all meaningful changes. Review periodically:

```bash
# Query recent audit entries (via docker)
docker compose -p eits --env-file .env -f deploy/docker-compose.yml exec postgres \
  psql -U eits -d eits -c "
SELECT created_at, actor_user_id, action, entity_type, entity_id
FROM audit_logs
WHERE created_at > NOW() - INTERVAL '7 days'
ORDER BY created_at DESC
LIMIT 50;"
```

What to look for:

- Suspicious `action` values (e.g., unexpected role grants at unusual hours)
- Failed authentication attempts (if logged)
- Repeated access to evidence files
- Unusual patterns in IMR status changes or risk acceptance

### 7.3 File Upload Security

Review evidence file uploads periodically:

- Verify no unexpected file types are stored in MinIO
- Check that evidence files are properly linked and not orphaned
- Confirm MinIO bucket access policies remain private

### 7.4 Compliance Checks

Run these checks quarterly:

- [ ] All active users have appropriate roles (no orphaned admin accounts)
- [ ] JWT token lifetime is not excessively long (`ACCESS_TOKEN_EXPIRE_MINUTES`)
- [ ] PostgreSQL and Redis are not exposed to public network (they should be internal Docker network only)
- [ ] TLS certificate is valid and configured if using HTTPS
- [ ] `.env` file contains no placeholder or default passwords
- [ ] All Docker images are up to date with latest security patches
- [ ] Backup restore has been tested within the last 30 days
- [ ] Audit log is enabled and capturing expected events

---

## 8. Troubleshooting Quick Reference

| Symptom | Likely Cause | Check |
|---|---|---|
| Backend unhealthy | Stale postgres password | Logs: `docker compose logs backend`; deploy script auto-detects |
| 502 Bad Gateway | Backend container down | `docker compose ps`; check if `eits_backend` is running |
| Cannot upload evidence | MinIO credentials changed | Check `MINIO_ACCESS_KEY` / `MINIO_SECRET_KEY` in `.env` |
| Slow page loads | Missing DB index | Run `EXPLAIN ANALYZE` on slow query; check `pg_stat_user_tables` |
| Login fails after deploy | JWT secret changed | All tokens invalidated; log in again |
| Disk space critical | Docker logs or unused images | `docker system df`; prune with `docker system prune -a` |

---

## 9. Related Documents

| Document | Location |
|---|---|
| Deployment guide | `deploy/README.md` |
| Teardown script | `deploy/clear.sh` |
| Architecture overview | `docs/architecture/overview.md` |
| Database migrations SOP | `docs/sop/database-migrations.md` |
| Backup SOP (deployment) | `deploy/README.md#backup` |
