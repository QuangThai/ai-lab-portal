#!/usr/bin/env bash
# Preflight checks before Playwright E2E (Harness backlog #13).
#
# Ensures Docker is reachable, Postgres/Redis infra is up, migrations are applied,
# and warns when compose app services may cause ADMIN_BOUNDARY_SECRET mismatches.
#
# Usage (from repo root):
#   scripts/e2e-preflight.sh
#   scripts/e2e-preflight.sh --skip-migrate

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

SKIP_MIGRATE=0
for arg in "$@"; do
  case "$arg" in
    --skip-migrate) SKIP_MIGRATE=1 ;;
    -h|--help)
      echo "Usage: scripts/e2e-preflight.sh [--skip-migrate]"
      echo ""
      echo "Start Postgres/Redis, wait for host port, run Alembic migrations."
      echo "See docs/local-dev.md for E2E secret alignment (backlog #14)."
      exit 0
      ;;
    *)
      echo "Unknown option: $arg" >&2
      exit 2
      ;;
  esac
done

POSTGRES_PORT="${POSTGRES_HOST_PORT:-15432}"
if [[ -f .env ]]; then
  val="$(grep -E '^POSTGRES_HOST_PORT=' .env | tail -1 | cut -d= -f2- | tr -d '\r" ' || true)"
  if [[ -n "$val" ]]; then
    POSTGRES_PORT="$val"
  fi
fi

fail() {
  echo "e2e-preflight: ERROR: $*" >&2
  exit 1
}

warn() {
  echo "e2e-preflight: WARN: $*" >&2
}

step() {
  echo "==> $*"
}

if ! command -v docker >/dev/null 2>&1; then
  fail "docker not found in PATH. Install Docker Desktop and retry."
fi

if ! docker info >/dev/null 2>&1; then
  fail "Docker daemon is not running. Start Docker Desktop, then retry."
fi

step "docker compose up -d postgres redis"
docker compose up -d postgres redis

step "wait for Postgres on localhost:${POSTGRES_PORT}"
if command -v python >/dev/null 2>&1; then
  PYTHON=python
elif command -v python3 >/dev/null 2>&1; then
  PYTHON=python3
else
  fail "python not found; needed to poll Postgres port"
fi

"$PYTHON" - <<PY
import socket
import sys
import time

host = "127.0.0.1"
port = int("${POSTGRES_PORT}")
deadline = time.monotonic() + 60
last_error = "not attempted"
while time.monotonic() < deadline:
    try:
        with socket.create_connection((host, port), timeout=2):
            print(f"postgres reachable on {host}:{port}")
            sys.exit(0)
    except OSError as exc:
        last_error = str(exc)
        time.sleep(1)
print(f"postgres not reachable on {host}:{port}: {last_error}", file=sys.stderr)
sys.exit(1)
PY

if [[ "$SKIP_MIGRATE" -eq 0 ]]; then
  step "alembic upgrade head"
  "$PYTHON" -m alembic -c backend/alembic.ini upgrade head
else
  step "skip migrations (--skip-migrate)"
fi

if docker compose ps --status running 2>/dev/null | grep -qE '(^|[[:space:]])backend([[:space:]]|$)|(^|[[:space:]])frontend([[:space:]]|$)'; then
  warn "compose backend/frontend are running; Playwright may hit the wrong ADMIN_BOUNDARY_SECRET."
  warn "Stop app services: docker compose stop backend frontend worker"
  warn "Then run E2E: cd frontend && CI=1 E2E_PORT=13100 npm run test:e2e"
fi

echo "==> e2e preflight passed (Postgres:${POSTGRES_PORT}, migrations:$([[ "$SKIP_MIGRATE" -eq 0 ]] && echo applied || echo skipped))"
