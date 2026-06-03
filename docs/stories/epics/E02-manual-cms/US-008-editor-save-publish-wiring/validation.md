# Validation

## Proof Strategy

Prove editor actions use a server-side Next.js boundary and keep backend admin API proof green.

## Test Plan

| Layer | Cases |
| --- | --- |
| Unit | Frontend action/client helpers build payloads and reject missing session where testable. |
| Integration | Backend admin blog API tests continue to prove authorization, publish visibility, and audit. |
| E2E | Editor route remains protected; save/publish UI renders. |
| Platform | Frontend typecheck/lint/build pass with server actions or route handlers. |
| Security | No admin boundary secret is exposed to client bundles. |

## Fixtures

- Draft editor content.
- Better Auth session fixture if server action tests are added.

## Commands

```text
python -m pytest backend/tests
cd frontend && npm run test && npm run typecheck && npm run lint && npm run build && npm run test:e2e
```

## Acceptance Evidence

- 2026-06-02 US-008 editor save and publish API wiring:
  - Added Next.js server actions for save draft and publish.
  - Server actions check Better Auth session and create signed FastAPI admin identity headers server-side.
  - Browser editor form submits content to server actions and never receives `ADMIN_BOUNDARY_SECRET`.
  - `python -m pytest backend/tests` → passed: 23 tests.
  - `cd frontend && npm run test && npm run typecheck && npm run lint && npm run build && npm run test:e2e` → passed.
  - `scripts/bin/harness-cli.exe story verify US-008` → passed the full configured verification command.
  - E2E continues to cover unauthenticated editor redirect to `/admin/login`.
