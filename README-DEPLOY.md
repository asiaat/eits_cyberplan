# Deploy to Hostinger — Manual Guide

This guide walks through deploying the E-ITS app to a Hostinger VPS step by step.
It covers the manual flow (SSH in, build, run, seed) — no magic scripts, just
plain commands with explanations of what each one does.

> **Who is this for?** Someone comfortable in a terminal who wants to understand
> what's happening under the hood rather than running a one-click deploy script.
> If you want the quick automated version, see `deploy/README.md` and the
> `deploy/deploy.sh` script.

---

## Prerequisites

- A Hostinger VPS (Ubuntu) with root SSH access
- The server's public IP address (find it in Hostinger hPanel → VPS → your VPS)
- An SSH key or root password
- Your project code pushed to GitHub (or accessible on the server)

---

## Step 1 — SSH into the Server

```bash
ssh root@<vps-ip-address>
```

You'll be prompted for the root password (the one you set in Hostinger hPanel
when ordering the VPS). Paste it and press Enter.

You should see a prompt like:
```
root@srv1073565:~#
```

You're now on the server. Every remaining command in this guide runs on the
server, not your local machine.

---

## Step 2 — Get the Code onto the Server

### Option A: Clone from GitHub (easiest)

```bash
mkdir -p /opt/eits
cd /opt/eits
git clone <your-repo-url> .
```

Replace `<your-repo-url>` with your Git repository URL. If the repo is private,
you'll need to authenticate (SSH key or personal access token).

After cloning, verify the files are there:
```bash
ls
# You should see: AGENT.md  Makefile  backend/  deploy/  docker-compose.yml  frontend/  ...
```

### Option B: SCP from your local machine

On your **local machine** (in a separate terminal), run:

```bash
scp -r /path/to/your/eits_cyberplan root@<vps-ip>:/opt/eits
```

Or faster for repeat copies (only sends changed files):

```bash
rsync -avz --progress /path/to/your/eits_cyberplan/ root@<vps-ip>:/opt/eits/
```

Then back on the server, verify:
```bash
ls /opt/eits
```

---

## Step 3 — Create the `.env` File

The app needs environment variables to run. Copy the example file and edit it:

```bash
cp /opt/eits/.env.example /opt/eits/.env
nano /opt/eits/.env
```

At minimum, change these values (generate random strings for secrets):

```bash
# Generate a random password/secret:
openssl rand -hex 32    # use this for POSTGRES_PASSWORD and JWT_SECRET_KEY
openssl rand -hex 16    # use this for MINIO_ACCESS_KEY
openssl rand -hex 32    # use this for MINIO_SECRET_KEY
```

Fill in the `.env` file. The key variables:

| Variable | What to put |
|---|---|
| `POSTGRES_PASSWORD` | Random 64-char hex string |
| `DATABASE_URL` | `postgresql+psycopg://eits:<POSTGRES_PASSWORD>@postgres:5432/eits` |
| `JWT_SECRET_KEY` | Random 64-char hex string |
| `MINIO_ACCESS_KEY` | Random 32-char hex string |
| `MINIO_SECRET_KEY` | Random 64-char hex string |
| `BACKEND_CORS_ORIGINS` | `http://<vps-ip>:5071` (or your domain later) |
| `VITE_API_URL` | `/api/v2` (keep the default) |

Save and exit (`Ctrl+O`, Enter, `Ctrl+X` in nano).

---

## Step 4 — Build the Docker Images

```bash
cd /opt/eits
docker compose -p eits --env-file .env -f deploy/docker-compose.yml build
```

This reads the `deploy/docker-compose.yml` file and builds:
- **backend** — Python FastAPI app (from `infra/docker/backend.Dockerfile`)
- **nginx** — Serves the built frontend + reverse-proxies API calls (from `infra/docker/frontend.Dockerfile`)

The `-p eits` flag sets the project name so all containers are prefixed with
`eits_`. The `--env-file .env` loads your configuration.

Building takes a few minutes the first time (downloading base images, installing
Python/Node dependencies). Subsequent builds are faster because layers are
cached.

---

## Step 5 — Start the Containers

```bash
docker compose -p eits --env-file .env -f deploy/docker-compose.yml up -d
```

The `-d` flag runs containers in the background (detached mode).

This starts 5 services:

| Container | Purpose |
|---|---|
| `eits_postgres` | PostgreSQL database — stores all app data |
| `eits_redis` | Redis cache — session storage, queues |
| `eits_minio` | MinIO object storage — evidence file uploads |
| `eits_backend` | FastAPI backend — the API |
| `eits_nginx` | Nginx — serves frontend on port 5071, proxies `/api/v2` to the backend |

Check they're all running:

```bash
docker ps --format 'table {{.Names}}\t{{.Status}}'
```

Expected output — all should show "Up" or "Up (healthy)":

```
NAMES            STATUS
eits_postgres    Up (healthy)
eits_redis       Up (healthy)
eits_minio       Up (healthy)
eits_backend     Up
eits_nginx       Up
```

> **What is nginx doing?** It serves the pre-built React frontend as static
> files on port 5071. When your browser makes API calls to `/api/v2/*`, nginx
> forwards those to the backend on port 8000 (internal — not exposed to the
> internet). This is why you only access the app through nginx on port 5071.

---

## Step 6 — Seed the Admin User

The database tables are created automatically by the backend entrypoint
(running `alembic upgrade head`). But the initial admin user needs to be
seeded explicitly:

```bash
docker compose -p eits --env-file .env -f deploy/docker-compose.yml exec backend \
  .venv/bin/python -m app.db.init_db
```

This runs the `init_db.py` script inside the backend container, which creates
the default roles, permissions, and admin user.

The default admin credentials are defined in
`backend/app/db/init_db.py`. Check that file to know the email and
password.

---

## Step 7 — Verify the App is Accessible

From your **local machine** (not the server), open a browser and go to:

```
http://<vps-ip>:5071
```

You should see the E-ITS login page.

From the server itself, you can also check:

```bash
curl http://localhost:5071/api/v2/health
```

Expected response:
```json
{"status":"healthy"}
```

---

## If Something Goes Wrong

### Check container logs

```bash
# All services
docker compose -p eits --env-file .env -f deploy/docker-compose.yml logs --tail=50

# Just one service (e.g., backend)
docker compose -p eits --env-file .env -f deploy/docker-compose.yml logs --tail=50 backend
```

### Restart a service

```bash
docker compose -p eits --env-file .env -f deploy/docker-compose.yml restart backend
```

### Rebuild after code changes

```bash
cd /opt/eits && git pull
docker compose -p eits --env-file .env -f deploy/docker-compose.yml build
docker compose -p eits --env-file .env -f deploy/docker-compose.yml up -d
```

### Stop everything

```bash
docker compose -p eits --env-file .env -f deploy/docker-compose.yml down
```

Data is preserved in Docker volumes (`eits_postgres_data`, `eits_redis_data`,
`eits_minio_data`). To also delete all data, add `-v`:

```bash
docker compose -p eits --env-file .env -f deploy/docker-compose.yml down -v
```

---

## Quick Reference

| Action | Command |
|---|---|
| Build images | `docker compose -p eits --env-file .env -f deploy/docker-compose.yml build` |
| Start all services | `docker compose -p eits --env-file .env -f deploy/docker-compose.yml up -d` |
| View logs | `docker compose -p eits --env-file .env -f deploy/docker-compose.yml logs -f` |
| Seed admin user | `docker compose -p eits --env-file .env -f deploy/docker-compose.yml exec backend .venv/bin/python -m app.db.init_db` |
| Rebuild & restart | `git pull && docker compose -p eits --env-file .env -f deploy/docker-compose.yml up -d --build` |
| Stop (keep data) | `docker compose -p eits --env-file .env -f deploy/docker-compose.yml down` |
| Stop & wipe data | `docker compose -p eits --env-file .env -f deploy/docker-compose.yml down -v` |
| Check status | `docker ps --format 'table {{.Names}}\t{{.Status}}'` |

---

## How It All Fits Together

Architecture once deployed:

```
Browser ──► nginx (:5071)
               ├── / ─────────────► static frontend files (React SPA)
               ├── /api/v2/* ─────► backend:8000 (FastAPI)
               │                      ├── postgres:5432 (database)
               │                      ├── redis:6379 (cache)
               │                      └── minio:9000 (file storage)
               └── /docs ─────────► backend:8000 (Swagger UI)
```

Only nginx's port (5071) is exposed to the outside world. All internal services
(postgres, redis, minio, backend) talk to each other over Docker's internal
network and are not reachable from outside the server.

---

## Next Steps (Optional)

- **Set up a domain** — point an A record to your VPS IP, then configure nginx
  with your domain name
- **Add HTTPS** — install Certbot, get a Let's Encrypt certificate, enable TLS
  in nginx
- **Configure the firewall** — ensure only port 5071 (HTTP) and 22 (SSH) are
  open; close everything else
- **Set up automatic backups** — schedule `pg_dump` via cron to back up the
  database nightly
