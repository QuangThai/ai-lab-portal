# Validation

## Proof Strategy

Prove the slice with backend API tests, migration generation tests, frontend build/type/lint/tests, and public page E2E coverage.

## Test Plan

| Layer | Cases |
| --- | --- |
| Unit | Blog response schemas validate published post fields. |
| Integration | List endpoint excludes drafts; detail endpoint returns published posts and 404 for drafts/missing slugs. |
| E2E | `/blog` and `/blog/[slug]` render public blog content. |
| Platform | Alembic and Next.js build checks pass. |
| Performance | Public pages remain static/cache-friendly where practical. |
| Logs/Audit | No draft content or secrets are logged. |

## Fixtures

- One published AI Lab post.
- One draft post excluded from public endpoints.

## Commands

```text
python -m pytest backend/tests
cd frontend && npm run test && npm run typecheck && npm run lint && npm run build && npm run test:e2e
```

## Acceptance Evidence

- 2026-06-02 US-005 published blog read model and public pages:
  - `python -m pytest backend/tests` → passed: 20 tests.
  - `cd frontend && npm run test && npm run typecheck && npm run lint && npm run build && npm run test:e2e` → passed.
  - Backend API tests cover published list, published detail, draft exclusion, and missing slug `404`.
  - Frontend E2E covers `/blog` and `/blog/building-an-ai-lab-with-human-review` rendering.
  - Next.js build prerenders `/blog` and SSG detail route for the published slug.
  - `scripts/bin/harness-cli.exe story verify US-005` → passed the full configured verification command.
