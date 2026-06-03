# Local Development

The repo supports two local workflows:

1. **Full Docker stack** — best for onboarding and smoke testing.
2. **Hybrid local dev** — best for day-to-day frontend/backend coding speed.

## Environment files

Templates:

- Root/backend: `.env.example`
- Backend-specific reference: `backend/.env.example`
- Frontend: `frontend/.env.example`

Recommended setup from repo root:

```bash
cp .env.example .env
cp frontend/.env.example frontend/.env.local
```

Backend `Settings(env_file=".env")` reads `.env` relative to the **process working directory**.
When commands run from repo root, backend/Alembic read root `.env`. If you `cd backend` before running Python, it reads `backend/.env` instead.

Docker Compose also reads root `.env` automatically for `${VARIABLE}` interpolation in `compose.yaml`. That does **not** mean every variable is automatically injected into containers; variables must be passed via `environment:` or `env_file:`. This repo uses explicit `environment:` mappings so container env is visible in `compose.yaml` and can still be overridden from root `.env`.

For how `.env` relates to `backend/Dockerfile` and `frontend/Dockerfile`, and what to set on a production server, see [docker-deployment.md](./docker-deployment.md).

---

## Mode A: Full Docker stack

Use this when onboarding, testing the full stack, or validating container wiring.

```bash
docker compose up --build
```

Services:

- Frontend: <http://127.0.0.1:13000>
- Backend health: <http://127.0.0.1:18000/health>
- Backend OpenAPI docs: <http://127.0.0.1:18000/docs>
- PostgreSQL: `localhost:15432`
- Redis: `localhost:16379`
- Celery worker and scheduler run in containers.

Container-internal URLs differ from host-local URLs:

| Purpose | Host/local URL | Docker internal URL |
| --- | --- | --- |
| Backend API | `http://127.0.0.1:18000` | `http://backend:8000` |
| PostgreSQL | `localhost:15432` | `postgres:5432` |
| Redis | `localhost:16379` | `redis:6379` |

`compose.yaml` maps frontend `BACKEND_INTERNAL_URL` from `${DOCKER_BACKEND_INTERNAL_URL:-http://backend:8000}` because Next.js server code runs inside the frontend container in full Docker mode. Keep host-local variables (`BACKEND_INTERNAL_URL=http://127.0.0.1:18000`) separate from Docker-internal variables (`DOCKER_BACKEND_INTERNAL_URL=http://backend:8000`).

Stop containers:

```bash
docker compose down
```

Use `docker compose down -v` only when you intentionally want to delete the local PostgreSQL volume.

---

## Mode B: Hybrid local dev

Use this for normal coding. Docker runs stateful infrastructure; backend/frontend run locally for faster reloads and easier debugging.

```bash
docker compose up -d postgres redis
```

From repo root, run backend:

```bash
python -m alembic -c backend/alembic.ini upgrade head
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 18000
```

In another terminal, run frontend:

```bash
cd frontend
npm run dev -- --hostname 127.0.0.1 --port 13000
```

If using Yarn after converting the package manager intentionally:

```bash
cd frontend
yarn dev --hostname 127.0.0.1 --port 13000
```

Current repo uses `package-lock.json`, so `npm` is the documented default.

---

## Validation commands

Backend:

```bash
python -m compileall -q backend
python -m pytest backend/tests
```

Frontend:

```bash
cd frontend
npm run test
npm run typecheck
npm run lint
npm run build
npm run test:e2e
```

React Doctor:

```bash
cd frontend
npx -y react-doctor@latest . --verbose
```

Compose config:

```bash
docker compose config --quiet
```

Full story verification example:

```bash
scripts/bin/harness-cli.exe story verify US-023
```

---

## Smoke commands

```bash
docker compose config --quiet
docker compose up --build -d postgres redis backend worker scheduler frontend
docker compose exec backend python -m alembic -c backend/alembic.ini current
docker compose exec backend python - <<'PY'
import urllib.request
print(urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=5).read().decode())
PY
docker compose exec backend python - <<'PY'
from backend.app.tasks import foundation_smoke
result = foundation_smoke.delay()
print(result.get(timeout=10))
PY
docker compose down
```
