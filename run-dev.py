#!/usr/bin/env python3
"""Start dev environment with proper logging."""
import subprocess, os, time
os.chdir("/Users/kalle/proj/asiaat/eits_cyberplan")
os.makedirs("logs", exist_ok=True)

def run(cmd, **kw): return subprocess.run(cmd, shell=True, capture_output=True, **kw)

for f in ["uvicorn", "vite"]:
    run(f"pkill -f '{f}'", check=False)
time.sleep(1)

print("Starting backend...")
be = subprocess.Popen(
    "cd backend && source .venv/activate && PYTHONPATH=. uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 > ../logs/backend.log 2>&1 &",
    shell=True, cwd=os.getcwd()
)
print(f"Backend background, waiting 5s...")
time.sleep(5)
r = run("curl -s http://localhost:8000/health")
print("Backend:", r.stdout.decode().strip() if r.returncode == 0 else "FAILED")

print("Starting frontend...")
fe = subprocess.Popen(
    "cd frontend && pnpm dev > ../logs/frontend.log 2>&1 &",
    shell=True, cwd=os.getcwd()
)
print(f"Frontend background, waiting 5s...")
time.sleep(5)

r = run("curl -s -o /dev/null -w '%{http_code}' http://localhost:5173")
code = r.stdout.decode().strip()
print(f"Frontend HTTP: {code}")
with open("logs/frontend.log") as f:
    log = f.read()
    if "error" in log.lower() or "fail" in log.lower():
        print("Frontend log tail:", log[-300:])
    elif not code or code == "000":
        print("Frontend log tail:", log[-300:])
print("\nReady: http://localhost:5173  |  http://localhost:8000/docs")