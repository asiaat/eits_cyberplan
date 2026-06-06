# Deploy — Pre-Live Environment

This directory contains everything needed to deploy the E-ITS Management System to a pre-live/production environment using Docker Compose.

## Contents

| File | Purpose |
|---|---|---|
| `docker-compose.yml` | Production service stack: nginx, backend, postgres, redis, minio |
| `nginx.conf` | Nginx config — serves the built frontend (SPA), reverse-proxies `/api` to the backend |
| `deploy.sh` | One-shot deployment script — installs Docker, clones repo, generates secrets, starts services |
| `clear.sh` | Teardown script — removes all containers/networks; optionally wipes data volumes |
| `.env.example` | Reference template for environment variables |
| `../infra/docker/backend-entrypoint.sh` | Backend container entrypoint — waits for postgres, runs migrations, seeds data, then starts uvicorn |

## Architecture

```
Browser ──► nginx (:5071)
               ├── / ───────────► static frontend files (built SPA)
               ├── /api/v2/* ───► backend:8000 (FastAPI)
               ├── /docs        ─► backend:8000 (Swagger UI)
               └── /health      ─► backend:8000
```

Only nginx exposes a port to the host. All other services (postgres, redis, minio, backend) are internal.

## Prerequisites

- **Hostinger VPS** (or any Ubuntu 22.04 VM) with root SSH access
- **SSH client** — on macOS/Linux use Terminal; on Windows use PowerShell or PuTTY
- **Port 5071 open** in the VPS firewall (you can check/configure this in Hostinger hPanel → Firewall)

## Step-by-Step Deployment

### Step 1: SSH into Your VPS

From your local machine, open a terminal and connect:

```bash
ssh root@<your-vps-ip-address>
```

You will be prompted for the root password (set in Hostinger hPanel when you ordered the VPS). Paste it and press Enter.

Once logged in, you should see a prompt like:
```
root@srv1073565:~#
```

> **Need to find your VPS IP?** Log into [Hostinger hPanel](https://hpanel.hostinger.com/), go to **VPS** → your VPS name. The IP is shown at the top of the page.

### Step 2: Choose How to Get the Code

You have two options:

#### Option A: Clone from GitHub (Recommended)

This is the simplest method. The deploy script can clone the repository automatically, or you can do it manually:

```bash
# One-command deploy — clones repo AND runs everything:
bash <(curl -sL https://raw.githubusercontent.com/asiaat/eits_cyberplan/main/deploy/deploy.sh)
```

This downloads and runs the deploy script directly from GitHub. The script will:
  1. Install Docker (if not present)
  2. Clone the repo into `/opt/eits`
  3. Deploy everything

#### Option B: Copy from Your Local Machine (SCP)

Use this if you have local changes that aren't pushed to GitHub, or if you prefer not to use GitHub.

On your **local machine**, open another terminal (keep the VPS SSH session open):

```bash
# From your local machine — scp the entire project to the VPS
scp -r /path/to/eits_cyberplan root@<vps-ip>:/opt/eits
```

Or using rsync (faster for repeated copies — only sends changed files):
```bash
rsync -avz --progress /path/to/eits_cyberplan/ root@<vps-ip>:/opt/eits/
```

Once the copy finishes, go back to your VPS SSH session and verify:
```bash
ls /opt/eits
# You should see: AGENT.md  Makefile  backend/  deploy/  docker-compose.yml  frontend/  ...
```

Then run the deploy script:
```bash
cd /opt/eits && bash deploy/deploy.sh
```

### Step 3: Run the Deploy Script

Whether you used Option A (one-liner) or Option B (manual copy + `bash deploy/deploy.sh`), the script will now run. The backend has a built-in entrypoint that automatically runs migrations and seeds the database on first start, so the deploy script is simpler than before.

Here is exactly what you will see:

```
[INFO]  Checking prerequisites...
[INFO]  Docker already installed.
[INFO]  Cloning repository into /opt/eits...
Cloning into '/opt/eits'...
remote: Enumerating objects: ...
[INFO]  Generating .env with random secrets...
[INFO]  .env generated.
[INFO]  Removing old containers...
[INFO]  Building and starting services (HTTP :5071)...
[+] Building 15.2s (15/15) FINISHED
[+] Running 5/5
 ✔ Container eits_postgres  Started
 ✔ Container eits_redis     Started
 ✔ Container eits_minio     Started
 ✔ Container eits_backend   Started
 ✔ Container eits_nginx     Started
[INFO]  Waiting for backend to be ready...
[INFO]  Backend is healthy.

============================================
  Deployment Complete!
============================================

  Access the application at:

  http://203.0.113.10:5071

  To view logs:
    docker compose --env-file .env -f deploy/docker-compose.yml logs -f

  To stop:
    docker compose --env-file .env -f deploy/docker-compose.yml down

  ┌─────────────────────────────────────────────────┐
  │  IMPORTANT: Save these credentials securely!    │
  │  They will not be shown again.                  │
  └─────────────────────────────────────────────────┘

  PostgreSQL password:  a1b2c3d4e5f6...
  JWT secret key:       f6e5d4c3b2a1...
  MinIO access key:     9a8b7c6d5e4f...
  MinIO secret key:     1a2b3c4d5e6f...
```

While the backend container starts, it automatically:
1. Waits for PostgreSQL to become ready
2. Runs `alembic upgrade head` (creates/updates tables)
3. Seeds default data (roles, permissions, admin user) if the database is empty
4. Starts uvicorn (the Python web server)

If the database already has data, steps 2-3 are safe to re-run — they are idempotent. If the database is fresh, the backend container will restart once (Docker's `restart: unless-stopped` policy) and the entrypoint retries automatically.

**Save the generated credentials** somewhere safe (like a password manager). They are shown only once.

### Step 4: Verify the Deployment

From your **local machine** (not the VPS), open a browser and go to:

```
http://<your-vps-ip>:5071
```

You should see the E-ITS CyberPlan login page. Log in with the seeded admin credentials:

> **Default demo credentials:** Check `backend/app/db/init_db.py` or the seed script output. Typically the seed creates an admin user with known credentials for testing.

To verify the backend is healthy:

```bash
# From your VPS SSH session:
curl http://localhost:5071/health
# Expected: {"status":"healthy","app":"eits-cyberplan"}
```

To check all containers are running:

```bash
docker compose --env-file .env -f /opt/eits/deploy/docker-compose.yml ps
```

Expected output:
```
NAME            IMAGE                       STATUS                    PORTS
eits_postgres   postgres:16-alpine          Up (healthy)              5432/tcp
eits_redis      redis:7-alpine              Up (healthy)              6379/tcp
eits_minio      minio/minio:latest          Up (healthy)              9000-9001/tcp
eits_backend    eits-cyberplan-backend      Up                        8000/tcp
eits_nginx      eits-cyberplan-nginx        Up                        0.0.0.0:5071->80/tcp
```

### Step 5: First Login

1. Open `http://<your-vps-ip>:5071` in your browser
2. Log in with the seeded default credentials
3. You should see the dashboard with demo data (organizations, business processes, assets, catalog modules, etc.)
4. Explore the application — try creating a business process, an asset, or viewing the E-ITS catalog

## Updating the Deployment

When code changes are pushed to GitHub, redeploy with:

```bash
# SSH into the VPS and run:
cd /opt/eits && git pull && bash deploy/deploy.sh
```

Or simply re-run the one-liner (it pulls the latest code automatically):
```bash
bash <(curl -sL https://raw.githubusercontent.com/asiaat/eits_cyberplan/main/deploy/deploy.sh)
```

The script is idempotent — existing data is preserved (database volumes, minio data). Only the application code and images are updated.

**Note:** `git pull` may fail if there are local changes (e.g., if you edited `.env` inside the repo). This is safe — the deploy script keeps your existing `.env` and only updates application code. To discard local changes: `cd /opt/eits && git stash && git pull`.

## Clearing / Redeploying from Scratch

If you need to start over (e.g., stale postgres password, corrupted data, or changing secrets):

### Quick Redeploy (containers only, keep all data)

```bash
cd /opt/eits && git pull && bash deploy/deploy.sh
```

The script force-removes old containers, rebuilds images, and restarts. Data volumes survive.

### Full Reset (delete everything and start fresh)

```bash
cd /opt/eits
bash deploy/clear.sh --volumes    # removes all containers, networks, AND data volumes
bash deploy/deploy.sh              # redeploys from scratch
```

### Selective Reset

Use the teardown script with different flags:

```bash
# Just clean up containers (keep data):
bash deploy/clear.sh

# Clean up containers + delete only the database:
bash deploy/clear.sh
docker volume rm eits_postgres_data
bash deploy/deploy.sh               # redeploy — fresh DB, old files/cache survive
```

### How Clearing Works

The `deploy/clear.sh` script does two things:

1. **Force-removes all eits containers by name** — catches orphaned containers even if they were created outside the compose project
2. **Tears down compose resources** — removes networks created by `docker compose`

With `--volumes` (or `-v`), it additionally removes:
- `eits_postgres_data` — PostgreSQL database
- `eits_redis_data` — Redis cache
- `eits_minio_data` — MinIO evidence files

This is also available via the Makefile:

```bash
make prod-clear        # remove containers + networks only
make prod-clear ARGS=--volumes   # full reset
```

### Automatic Stale Password Recovery

If the `.env` file was regenerated with a new `POSTGRES_PASSWORD` but the postgres data volume still has the old one, the deploy script detects this automatically:

1. Backend container fails to start with `password authentication failed`
2. After 120s timeout, the script checks the backend logs for this error
3. If detected, it wipes the postgres volume and restarts the stack
4. The backend then initializes with the new password

This recovery is printed as:
```
[WARN]  Checking for stale postgres password...
[WARN]  Postgres volume has a stale password. Wiping it and retrying...
[INFO]  Backend is healthy after volume reset.
```

## Manual Commands

Quick reference:

| Action | Command |
|---|---|
| Deploy | `bash deploy/deploy.sh` |
| Clear containers (keep data) | `bash deploy/clear.sh` |
| Full reset | `bash deploy/clear.sh --volumes` |
| View logs | `docker compose --env-file .env -f deploy/docker-compose.yml logs -f` |
| Stop (keep data) | `docker compose --env-file .env -f deploy/docker-compose.yml down` |
| Stop & delete data | `docker compose --env-file .env -f deploy/docker-compose.yml down -v` |

If you prefer to manage the services manually:

```bash
# Build images
docker compose --env-file .env -f deploy/docker-compose.yml build

# Start services with custom port
HTTP_PORT=5071 docker compose --env-file .env -f deploy/docker-compose.yml up -d

# View logs
docker compose --env-file .env -f deploy/docker-compose.yml logs -f

# Tail only backend logs
docker compose --env-file .env -f deploy/docker-compose.yml logs -f backend

# Run migrations manually (normally auto-run by entrypoint on container start)
docker compose --env-file .env -f deploy/docker-compose.yml exec backend alembic upgrade head

# Seed demo data manually (normally auto-run by entrypoint)
docker compose --env-file .env -f deploy/docker-compose.yml exec backend python -m app.db.init_db

# Stop all services (data is preserved in volumes)
docker compose --env-file .env -f deploy/docker-compose.yml down

# Stop and DELETE all data (volumes included) — be careful!
docker compose --env-file .env -f deploy/docker-compose.yml down -v

# Restart a single service (e.g., after config change)
docker compose --env-file .env -f deploy/docker-compose.yml restart backend
```

Or use the Makefile (the `--env-file .env` flag is baked into these targets):

```bash
make prod-build    # Build production images
make prod-up       # Start production stack
make prod-logs     # Tail production logs
make prod-down     # Stop production stack
make deploy        # Run full deploy script
```

## Ports

| Service | Default Port | Env Variable |
|---|---|---|
| HTTP (nginx) | `5071` | `HTTP_PORT` |
| HTTPS (nginx, when configured) | `5471` | `HTTPS_PORT` |

### Changing the Port

```bash
# During deployment:
HTTP_PORT=8080 bash deploy/deploy.sh

# Or after deployment (stop, recreate, restart):
HTTP_PORT=8080 docker compose --env-file .env -f deploy/docker-compose.yml up -d
```

If you change the port, also update `.env`:
```bash
# Edit /opt/eits/.env and update:
BACKEND_CORS_ORIGINS=http://<VPS_IP>:8080
```

## Files on the VPS

After deployment, the VPS file structure looks like:

```
/opt/eits/
├── .env                  # Generated secrets and configuration
├── deploy/
│   ├── docker-compose.yml
│   ├── nginx.conf
│   ├── deploy.sh
│   └── README.md
├── backend/              # Application code
├── frontend/             # Application code
├── infra/                # Dockerfiles
└── ... (other project files)
```

Docker volumes (persistent data, survives container restarts):
```
eits_postgres_data   → /var/lib/docker/volumes/eits_postgres_data/
eits_redis_data      → /var/lib/docker/volumes/eits_redis_data/
eits_minio_data      → /var/lib/docker/volumes/eits_minio_data/
```

## Environment Variables

The deploy script generates a `.env` file in `/opt/eits/.env` automatically. You can edit it after deployment if needed:

```bash
nano /opt/eits/.env     # Edit variables
docker compose --env-file .env -f /opt/eits/deploy/docker-compose.yml restart backend nginx  # Apply changes
```

Always use `--env-file .env` when running docker compose commands manually — this ensures the `.env` file from the repo root is used, even when the compose file is in the `deploy/` subdirectory. The `Makefile` and `deploy.sh` already include this flag automatically.

Key variables:

| Variable | Description |
|---|---|
| `POSTGRES_PASSWORD` | Random 64-char hex |
| `JWT_SECRET_KEY` | Random 64-char hex — used to sign auth tokens |
| `MINIO_ACCESS_KEY` | Random 32-char hex — MinIO root user |
| `MINIO_SECRET_KEY` | Random 64-char hex — MinIO root password |
| `BACKEND_CORS_ORIGINS` | Set to `http://<VPS_IP>:<HTTP_PORT>` |
| `VITE_API_URL` | `/api/v2` — frontend API base path |

## Adding TLS (When You Have a Domain)

1. Buy a domain and point its **DNS A record** to your VPS IP (this is done in your domain registrar's control panel)
2. Install certbot on the VPS:

```bash
apt install -y certbot python3-certbot-nginx
```

3. Obtain certificates:

```bash
certbot certonly --nginx -d yourdomain.com
```

4. Create cert directory and copy certificates:

```bash
mkdir -p /opt/eits/certs
cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem /opt/eits/certs/
cp /etc/letsencrypt/live/yourdomain.com/privkey.pem /opt/eits/certs/
chmod 600 /opt/eits/certs/privkey.pem
```

5. Edit `deploy/nginx.conf` on the VPS — uncomment the TLS lines (listen 443 ssl, ssl_certificate, ssl_certificate_key) and change `server_name _;` to `server_name yourdomain.com;`

6. Edit `deploy/docker-compose.yml` on the VPS — uncomment the HTTPS port mapping

7. Update `.env`:

```bash
# In /opt/eits/.env:
BACKEND_CORS_ORIGINS=https://yourdomain.com:5471
MINIO_SECURE=true
```

8. Rebuild and restart:

```bash
cd /opt/eits && docker compose --env-file .env -f deploy/docker-compose.yml up -d --build
```

Now access the app at **https://yourdomain.com:5471**

### Auto-Renewal

Let's Encrypt certs expire after 90 days. Set up auto-renewal:

```bash
# Test renewal
certbot renew --dry-run

# Add a cron job to renew and copy certs
crontab -e
# Add this line:
0 3 * * * certbot renew --quiet && cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem /opt/eits/certs/ && cp /etc/letsencrypt/live/yourdomain.com/privkey.pem /opt/eits/certs/ && docker compose --env-file .env -f /opt/eits/deploy/docker-compose.yml restart nginx
```

## Troubleshooting

### Container fails to start

```bash
# Check logs for the failing service:
docker compose --env-file .env -f deploy/docker-compose.yml logs backend
docker compose --env-file .env -f deploy/docker-compose.yml logs nginx
docker compose --env-file .env -f deploy/docker-compose.yml logs postgres
```

### Port already in use

If port 5071 is already taken by another service:

```bash
# Check what is using the port:
ss -tlnp | grep 5071

# Use a different port:
HTTP_PORT=8080 docker compose --env-file .env -f deploy/docker-compose.yml up -d
```

### Cannot connect to the app

1. Check if services are running: `docker compose --env-file .env -f deploy/docker-compose.yml ps`
2. Check the firewall: `ufw status` (if using ufw) or check Hostinger hPanel firewall rules
3. Ensure port 5071 is open in the VPS firewall

### Database connection error

```bash
# Check if postgres is healthy:
docker compose --env-file .env -f deploy/docker-compose.yml ps postgres

# Restart postgres if needed:
docker compose --env-file .env -f deploy/docker-compose.yml restart postgres

# Wait for it, then restart backend:
docker compose --env-file .env -f deploy/docker-compose.yml restart backend
```

### Forgot the admin password

The seed script creates a default admin user. Re-run it:

```bash
docker compose --env-file .env -f deploy/docker-compose.yml exec backend python -m app.db.init_db
```

Check `backend/app/db/init_db.py` for the default credentials.

### Out of disk space

```bash
# Check disk usage
df -h

# Clean up unused Docker images
docker system prune -a

# Remove old Docker build cache
docker builder prune
```

## Backup

### Database

```bash
# Create a backup
docker compose --env-file .env -f /opt/eits/deploy/docker-compose.yml exec -T postgres \
  pg_dump -U eits eits > /opt/eits/backups/backup_$(date +%Y%m%d_%H%M%S).sql

# Restore from backup
cat backup_file.sql | docker compose --env-file .env -f /opt/eits/deploy/docker-compose.yml exec -T postgres \
  psql -U eits eits
```

### Evidence Files (MinIO)

MinIO data is stored in the `eits_minio_data` Docker volume. Back it up:

```bash
# Create a backup of the MinIO volume
docker run --rm -v eits_minio_data:/source -v /opt/eits/backups:/backup alpine \
  tar czf /backup/minio_backup_$(date +%Y%m%d).tar.gz -C /source .
```

## Full Reset

To wipe everything and start fresh:

```bash
cd /opt/eits
docker compose --env-file .env -f deploy/docker-compose.yml down -v   # Stops services and deletes volumes
rm .env                                                 # Remove secrets
bash deploy/deploy.sh                                   # Redeploy from scratch
```

> **Warning:** This deletes all data — database, evidence files, and Redis cache.
