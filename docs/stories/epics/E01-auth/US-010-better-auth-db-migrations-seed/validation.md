# Validation

## Proof Strategy

Prove Better Auth persistence strategy without weakening auth.

## Test Plan

| Layer | Cases |
| --- | --- |
| Unit | Seed helper refuses production mode. |
| Integration | Better Auth can create/sign in deterministic admin after schema exists. |
| E2E | Later US-009 uses this fixture for login/editor flow. |
| Platform | Frontend typecheck/lint/build pass. |
| Security | No production bypass or browser-exposed secrets. |

## Commands

```text
python -m pytest backend/tests
cd frontend && npm run test && npm run typecheck && npm run lint && npm run build && npm run test:e2e
```

## Acceptance Evidence

- 2026-06-02 US-010 Better Auth DB migrations and admin seed:
  - Researched official Better Auth CLI with Context7 and local `npx auth generate --help`.
  - Generated PostgreSQL/Kysely schema using `npx auth generate --config lib/auth/server.ts --output ../tmp-better-auth-schema.sql --adapter kysely --dialect postgresql --yes` and converted it into project-owned Alembic migration `20260602_0004_better_auth_tables.py`.
  - Added guarded `frontend/scripts/seed-admin.mjs` that calls the real Better Auth sign-up API and refuses production/non-explicit seed mode.
  - Added `npm run seed:admin`.
  - `python -m pytest backend/tests` → passed: 23 tests.
  - `cd frontend && npm run test && npm run typecheck && npm run lint && npm run build && npm run test:e2e` → passed.
  - `scripts/bin/harness-cli.exe story verify US-010` → passed the full configured verification command.
