# Validation

## Proof Strategy

Prove authenticated editor E2E without weakening the accepted Better Auth and FastAPI admin boundary decisions.

## Test Plan

| Layer | Cases |
| --- | --- |
| Unit | Fixture helper refuses to run outside explicit test/E2E mode. |
| Integration | Better Auth deterministic admin can obtain a real session. |
| E2E | Login redirects to authenticated admin/editor route; editor fields and buttons render; save/publish path is exercised if backend is deterministic. |
| Security | No production auth bypass, no browser-exposed admin boundary secret. |
| Platform | Full backend/frontend verification passes. |

## Commands

```text
python -m pytest backend/tests
cd frontend && npm run test && npm run typecheck && npm run lint && npm run build && npm run test:e2e
```

## Acceptance Evidence

- 2026-06-02 US-009 authenticated editor E2E fixture:
  - Applied Alembic migrations to local Postgres with `AI_LAB_DATABASE_URL=postgresql+psycopg://ai_lab:ai_lab_dev_password@localhost:15432/ai_lab_portal python -m alembic -c backend/alembic.ini upgrade head`.
  - Added Playwright authenticated admin fixture using real Better Auth `sign-up/email` and `sign-in/email` API calls with the required trusted `Origin` header.
  - Uses a unique admin email per run to avoid stale password/state collisions.
  - E2E proves an authenticated admin can open `/admin/blog/editor` and see editor fields/actions.
  - `python -m pytest backend/tests` → passed: 23 tests.
  - `cd frontend && npm run test && npm run typecheck && npm run lint && npm run build && npm run test:e2e` → passed; E2E `6 passed`.
  - `scripts/bin/harness-cli.exe story verify US-009` → passed the full configured verification command.
