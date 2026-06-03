# Validation

## Proof Strategy

Prove data persistence, authorization, publish visibility, and audit attribution at API level before adding rich admin UI.

## Test Plan

| Layer | Cases |
| --- | --- |
| Unit | Blog request/response schemas validate required fields and slug/status constraints. |
| Integration | Admin endpoints reject missing/invalid identity; admin can create/update/publish/unpublish; public endpoints expose only published persisted posts. |
| Audit | Create/update/publish/unpublish write actor-attributed audit events without secrets or raw identity envelopes. |
| E2E | Existing public blog and admin auth smoke tests continue to pass; add UI E2E only if UI changes. |
| Platform | Alembic migration and full backend/frontend verification pass. |
| Logs | No cookies, shared secrets, passwords, or raw signed headers are logged. |

## Fixtures

- Deterministic admin identity fixture signed with test boundary secret.
- Draft post fixture.
- Published post fixture.

## Commands

```text
python -m pytest backend/tests
cd frontend && npm run test && npm run typecheck && npm run lint && npm run build && npm run test:e2e
```

## Acceptance Evidence

- 2026-06-02 US-006 admin blog CRUD publishing and audit:
  - `python -m pytest backend/tests` → passed: 23 tests.
  - `cd frontend && npm run test && npm run typecheck && npm run lint && npm run build && npm run test:e2e` → passed.
  - `scripts/bin/harness-cli.exe story verify US-006` → passed the full configured verification command.
  - Backend tests cover missing admin identity rejection, create/update/publish/unpublish, public visibility changes, missing post `404`, and actor-attributed audit events.
  - Rich admin editor UI remains out of scope; API-level persistence/mutation contract is proven first.
