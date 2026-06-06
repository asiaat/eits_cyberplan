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
.venv/bin/alembic upgrade head
echo "Migrations complete."

echo "Seeding demo data..."
.venv/bin/python -m app.db.init_db || echo "Seeding failed (may already have data)."
echo "Seeding complete."

exec "$@"
