# Validation

## Proof Strategy

Prove the story with frontend unit/type/lint/build checks and E2E coverage for the admin auth shell behavior.

## Test Plan

| Layer | Cases |
| --- | --- |
| Unit | Auth environment/config helpers continue to validate required settings. |
| Integration | Better Auth route remains available through the Next.js route handler. |
| E2E | Unauthenticated admin access redirects to login; login page renders without exposing secrets. |
| Platform | Next.js production build succeeds with the auth route and protected admin route. |
| Performance | Not required for this small admin shell slice. |
| Logs/Audit | No secrets, passwords, session tokens, or cookies are logged. |

## Fixtures

- Local Better Auth environment placeholders from `frontend/.env.example` or test-specific environment.
- A deterministic test user may be added only if needed for login success E2E coverage.

## Commands

```text
cd frontend && npm run test
cd frontend && npm run typecheck
cd frontend && npm run lint
cd frontend && npm run build
cd frontend && npm run test:e2e
```

## Acceptance Evidence

- 2026-06-02 US-003 login UI/protected admin shell:
  - `cd frontend && npm run test && npm run typecheck && npm run lint && npm run build` → passed.
  - `cd frontend && npm run test:e2e` → passed after stopping a pre-existing Next dev server on PID 6056 that blocked Playwright startup.
  - E2E covers public shell rendering, unauthenticated `/admin` redirect to `/admin/login`, and login form rendering.
  - `scripts/bin/harness-cli.exe story verify US-003` → passed the full configured verification command.
  - `srcwalk review --scope frontend` could not run because this workspace is not a Git repository; validation relied on targeted srcwalk reads plus executable checks.
