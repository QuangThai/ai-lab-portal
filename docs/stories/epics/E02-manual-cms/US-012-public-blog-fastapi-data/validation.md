# Validation

## Proof Strategy

Prove public pages read FastAPI data and the authenticated publish flow becomes publicly visible.

## Commands

```text
python -m pytest backend/tests
cd frontend && npm run test && npm run typecheck && npm run lint && npm run build && npm run test:e2e
```

## Acceptance Evidence

- 2026-06-02 US-012 public blog reads FastAPI data:
  - Replaced frontend static blog seed reads with server-side fetches to FastAPI public endpoints.
  - `/blog` and `/blog/[slug]` are dynamic/no-store for MVP proof.
  - Authenticated editor E2E now publishes a post, navigates to `/blog`, and asserts the newly published title appears publicly.
  - `python -m pytest backend/tests` → passed: 23 tests.
  - `cd frontend && npm run test && npm run typecheck && npm run lint && npm run build && npm run test:e2e` → passed; E2E `6 passed`.
  - `scripts/bin/harness-cli.exe story verify US-012` → passed the full configured verification command.
