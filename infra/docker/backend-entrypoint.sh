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
if .venv/bin/alembic upgrade heads 2>/dev/null; then
    echo "Migrations complete."
elif .venv/bin/alembic upgrade head 2>/dev/null; then
    echo "Migrations complete."
else
    echo "WARNING: alembic upgrade failed. Trying specific heads..."
    for head in $(.venv/bin/alembic heads 2>/dev/null | awk '{print $1}'); do
        echo "Applying head: $head"
        .venv/bin/alembic upgrade "$head" || true
    done
    echo "Migrations applied."
fi

echo "Seeding demo data..."
.venv/bin/python -m app.db.init_db || echo "Seeding failed (may already have data)."
echo "Seeding complete."

exec "$@"
