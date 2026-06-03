# Validation

## Proof Strategy

Prove the boundary at API level before building privileged product behavior:

- Backend unit/integration tests cover missing, malformed, invalid, and valid identity envelopes.
- Frontend tests continue to prove admin authentication shell behavior.
- If a Next.js server proxy is added, E2E or integration coverage proves unauthenticated users cannot reach protected boundary behavior.

## Test Plan

| Layer | Cases |
| --- | --- |
| Unit | FastAPI boundary parser validates required identity fields, roles, and signature/secret material without leaking secrets. |
| Integration | Protected FastAPI admin probe rejects missing/invalid identity and accepts a valid server-generated identity. |
| E2E | Existing admin login/protection tests continue to pass; add browser-visible coverage only if UI changes. |
| Platform | Backend and frontend build/test commands pass. |
| Performance | Not required for this boundary smoke slice. |
| Logs/Audit | No cookies, shared secrets, raw tokens, passwords, or full identity envelopes are logged. |

## Fixtures

- Deterministic admin identity fixture.
- Test-only boundary secret or signing key.
- Non-admin/invalid role fixture.

## Commands

Initial expected commands:

```text
python -m pytest backend/tests
cd frontend && npm run test && npm run typecheck && npm run lint && npm run build && npm run test:e2e
```

Update commands after implementation discovery if a narrower or stronger proof path is available.

## Acceptance Evidence

- 2026-06-02 US-004 admin roles and FastAPI identity boundary:
  - User confirmed HMAC headers and `admin`-only MVP role.
  - `python -m pytest backend/tests` → passed: 17 tests.
  - `cd frontend && npm run test && npm run typecheck && npm run lint && npm run build && npm run test:e2e` → passed.
  - Backend tests cover missing, tampered, non-admin, expired, and valid admin identity envelopes.
  - Frontend unit tests cover deterministic signed admin identity header creation.
  - `scripts/bin/harness-cli.exe story verify US-004` → passed the full configured verification command.
