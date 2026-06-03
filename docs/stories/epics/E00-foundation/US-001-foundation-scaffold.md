# US-001 Foundation Scaffold

## Status

implemented

## Lane

high-risk

## Product Contract

Create the minimum application foundation for AI Lab Portal: frontend shell,
backend health/API docs, database migration path, Redis/Celery smoke path,
environment validation, local orchestration, and structured logging. This story
does not implement domain CMS, auth, publishing, crawling, or AI behavior.

## Relevant Product Docs

- `docs/product/overview.md`
- `docs/product/architecture.md`
- `docs/product/mvp-roadmap.md`
- `docs/decisions/0006-ai-lab-portal-mvp-architecture.md`

## Acceptance Criteria

- FastAPI backend exposes a health endpoint that returns service status.
- Backend OpenAPI docs are available in development.
- Next.js frontend renders a public/admin base shell without domain data.
- PostgreSQL connection settings are validated from environment and Alembic can
  run from an empty database.
- Redis connection settings are validated from environment.
- Celery worker can execute a smoke-test job.
- Structured JSON logs include timestamp, level, request id when applicable,
  action/message, duration/status for requests where available.
- Docker Compose can run local Postgres, Redis, backend, worker, scheduler, and
  frontend or documents any intentionally deferred process.
- Secrets are loaded from environment variables and no secret values are
  committed.

## Design Notes

- Commands: health check, migration command, worker smoke command, frontend dev
  command, quick validation command once scripts exist.
- Queries: none beyond health/smoke checks.
- API: `GET /health` only for this story.
- Tables: migration infrastructure only; no domain tables yet.
- Domain rules: no domain behavior in this story.
- UI surfaces: base public shell and base admin shell only; admin auth is not in
  scope for this story.

## Validation

Durable proof status is tracked with:
`scripts/bin/harness-cli story update --id US-001 --unit 1 --integration 1 --e2e 1 --platform 1`.

Story verify command:
`python scripts/validate_foundation.py`.

| Layer | Expected proof |
| --- | --- |
| Unit | Environment/settings validation tests and logging formatter tests once code exists. |
| Integration | Health endpoint, Alembic migration against empty Postgres, Redis ping, Celery smoke job. |
| E2E | Frontend shell renders in browser after frontend exists. |
| Platform | Docker Compose smoke for local runtime. |
| Release | Quick validation command once package scripts exist. |

## Harness Delta

- Product docs were extracted from `SPEC.md` before implementation.
- Durable story row should track foundation proof status.
- Auth/provider/social ingestion decisions are explicitly deferred.

## Evidence

- 2026-06-01 Task 1 backend health/settings scaffold:
  `python -m pytest backend/tests` → 4 passed. Covers FastAPI `/health`, `/docs`,
  settings defaults, and blank environment validation.
- 2026-06-01 Task 2 request logging scaffold:
  `python -m pytest backend/tests` → 6 passed. Covers request id reuse,
  request id generation, sanitized JSON request log shape, health, docs, and
  settings validation.
- 2026-06-02 Task 3 frontend shell scaffold:
  `cd frontend && npm run typecheck && npm run lint && npm run build` → passed.
  Covers TypeScript, ESLint, and production build for public `/` and admin
  `/admin` placeholder shells.
- 2026-06-02 Task 4 PostgreSQL/Alembic foundation:
  `python -m pytest backend/tests` → 9 passed. Covers PostgreSQL DSN settings
  validation and empty Alembic foundation head with no domain tables.
  `python -m alembic -c backend/alembic.ini upgrade head --sql` → passed.
  Generates PostgreSQL migration SQL for the empty foundation revision; online
  empty-database migration proof remains pending local Postgres orchestration.
- 2026-06-02 Task 5 Redis/Celery smoke foundation:
  `python -m pytest backend/tests` → 12 passed. Covers Redis DSN settings
  validation, Celery Redis broker/result configuration, and eager smoke task
  execution.
  `python - <<'PY' ... foundation_smoke.delay().get(timeout=1)` → returned
  `{'status': 'ok', 'task': 'foundation.smoke'}`. Real Redis worker execution
  remains pending local Redis orchestration.
- 2026-06-02 Task 6 Docker Compose local orchestration:
  `docker compose config --quiet` → passed.
  `python -m pytest backend/tests` → 12 passed.
  `cd frontend && npm run typecheck` → passed.
  `docker compose up --build -d postgres redis backend worker scheduler frontend`
  → passed after moving host ports to non-default `15432`, `16379`, `18000`,
  and `13000` to avoid local collisions.
  `docker compose exec -T backend python -m alembic -c backend/alembic.ini current`
  → `20260602_0001 (head)`.
  Host health check at `http://127.0.0.1:18000/health` returned service status,
  frontend `http://127.0.0.1:13000/` returned HTTP 200, and a Celery smoke task
  through Redis/worker returned `{'status': 'ok', 'task': 'foundation.smoke'}`.
- 2026-06-02 Task 7 frontend browser/E2E smoke:
  `cd frontend && npx playwright install chromium && npm run typecheck && npm run lint && npm run build && npm run test:e2e`
  → typecheck, lint, and build passed; first E2E attempt failed because port
  `3000` was serving another local app (`Scopelytics`). After moving Playwright
  to `127.0.0.1:13000`, `npm run test:e2e` → 2 passed. Covers public `/` shell
  and `/admin` placeholder shell in Chromium.
  `agent-browser open/snapshot` verified the same public and admin headings in
  a real browser session at `http://127.0.0.1:13000`.
- 2026-06-02 Task 8 foundation closeout:
  Added `python scripts/validate_foundation.py` as the quick validation command.
  First run exposed Windows `npm` resolution and occupied E2E port issues; fixed
  the script to resolve `npm.cmd`/`docker.exe` and moved default Playwright E2E
  port to `127.0.0.1:13000`.
  `python scripts/validate_foundation.py` → passed. Covers Docker Compose config,
  backend tests, Alembic offline SQL generation, frontend typecheck, lint, build,
  and Playwright E2E smoke.
  `scripts/bin/harness-cli story verify US-001` → passed. Durable story status
  set to `implemented` with unit/integration/e2e/platform proof all marked yes.
