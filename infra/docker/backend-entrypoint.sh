#!/usr/bin/env bash
set -euo pipefail

echo "Waiting for PostgreSQL..."
for i in $(seq 1 30); do
    if pg_isready -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" &>/dev/null; then
        echo "PostgreSQL is ready."
        break
    fi
    if [ "$i" -eq 30 ]; then
        echo "ERROR: PostgreSQL did not become ready within 60 seconds."
        exit 1
    fi
    sleep 2
done

echo "Running database migrations..."
success=0
for attempt in 1 2 3; do
    if .venv/bin/alembic upgrade heads 2>/dev/null; then
        echo "Migrations complete (attempt $attempt)."
        success=1
        break
    fi
    echo "Migration attempt $attempt failed, retrying in 5s..."
    sleep 5
done
if [ "$success" -eq 0 ]; then
    echo "WARNING: Migrations did not complete successfully."
fi

echo "Seeding demo data..."
.venv/bin/python -m app.db.init_db || echo "Seeding failed (may already have data)."
echo "Seeding complete."

exec "$@"
