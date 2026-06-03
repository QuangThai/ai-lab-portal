# Validation

## Proof Strategy

Prove backend tests remain deterministic and E2E publish/public visibility works through a FastAPI runtime configured with Postgres.

## Commands

```text
python -m pytest backend/tests
cd frontend && npm run test && npm run typecheck && npm run lint && npm run build && npm run test:e2e
```

## Acceptance Evidence

- 2026-06-02 US-013 Postgres-backed blog repository:
  - Added SQLAlchemy engine helper and `PostgresBlogRepository` for non-test FastAPI runtime.
  - Kept deterministic in-memory `BlogRepository` for injected tests and `environment="test"`.
  - Runtime Postgres repository persists blog posts and audit events through existing `blog_posts` and `audit_events` tables.
  - Public default seed content is inserted lazily by slug if missing.
  - Playwright starts FastAPI with explicit local Docker Postgres URL on port `15432`.
  - `python -m pytest backend/tests` → passed: 23 tests.
  - `cd frontend && npm run test && npm run typecheck && npm run lint && npm run build && npm run test:e2e` → passed; E2E `6 passed`.
  - `scripts/bin/harness-cli.exe story verify US-013` → passed the full configured verification command.
