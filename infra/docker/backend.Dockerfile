FROM python:3.11-slim

WORKDIR /app/backend

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY backend /app/backend/
COPY infra/docker/backend-entrypoint.sh /app/backend/
RUN chmod +x /app/backend/backend-entrypoint.sh

RUN rm -rf .venv && \
    pip install --upgrade pip --no-cache-dir && \
    pip install uv --no-cache-dir && \
    uv sync

ENTRYPOINT ["/app/backend/backend-entrypoint.sh"]

RUN addgroup --system --gid 1001 appgroup && \
    adduser --system --uid 1001 --ingroup appgroup appuser && \
    chown -R appuser:appgroup /app

USER appuser

EXPOSE 8000

CMD [".venv/bin/python3", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
