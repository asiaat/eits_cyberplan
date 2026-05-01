#!/bin/ bash
set -e
cd "$(dirname "${BASH_ SOURCE[0]}")"
mkdir -p logs
pkill -f "uvicorn.*8[0-9]{3}" 2>/dev/null || true
pkill -f "pnpm.*dev" 2>/dev/null || true
pkill -f "vite" 2>/dev/null || true
sleep 1
echo "Starting backend on port 8000..."
(cd backend && source .venv/bin/activate && PYTHONPATH=. uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 >> ../logs/backend.log 2>&1) &
BACKEND_PID=$!
echo "Backend PID: $BACKEND_PID"
sleep 4
if curl -s --fail http://localhost:8000/health > /dev/null 2>&1; then
    echo "Backend: OK at http://localhost:8000"
else
    echo "Backend: FAILED"
    tail -10 logs/backend.log 2>/dev/null || echo "(no log)"
fi
echo "Starting frontend..."
cd frontend && pnpm dev >> ../logs/frontend.log 2>&1 &
echo "Frontend PID: $!"
sleep 3
echo ""
echo "=== Dev environment ==="
echo "Backend: http://localhost:8000  (logs/logs/backend.log)"
echo "Frontend: http://localhost:5173 (logs/logs/frontend.log)"
echo "OpenAPI: http://localhost:8000/docs"