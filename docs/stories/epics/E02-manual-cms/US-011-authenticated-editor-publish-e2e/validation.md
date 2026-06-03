# Validation

## Proof Strategy

Run full backend/frontend verification with an E2E that logs in and publishes from the editor.

## Commands

```text
python -m pytest backend/tests
cd frontend && npm run test && npm run typecheck && npm run lint && npm run build && npm run test:e2e
```

## Acceptance Evidence

- 2026-06-02 US-011 authenticated editor publish E2E:
  - Added visible editor action state using React `useActionState`.
  - Updated publish action to create-and-publish when no saved `postId` exists.
  - Updated Playwright to start FastAPI on `127.0.0.1:18000` alongside Next.js.
  - Authenticated E2E logs in through Better Auth, opens `/admin/blog/editor`, clicks `Publish saved post`, and asserts visible `Post published` status.
  - `python -m pytest backend/tests` → passed: 23 tests.
  - `cd frontend && npm run test && npm run typecheck && npm run lint && npm run build && npm run test:e2e` → passed; E2E `6 passed`.
  - `scripts/bin/harness-cli.exe story verify US-011` → passed the full configured verification command.
