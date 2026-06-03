# Validation

## Proof Strategy

Run full verification and prove authenticated admin can open `/admin/blog`.

## Commands

```text
python -m pytest backend/tests
cd frontend && npm run test && npm run typecheck && npm run lint && npm run build && npm run test:e2e
```

## Acceptance Evidence

- 2026-06-02 US-015 admin blog list management UI:
  - Added `GET /admin/blog-posts` requiring signed admin identity.
  - Added repository `list_all()` for in-memory and Postgres implementations.
  - Added protected Next.js `/admin/blog` page that checks Better Auth session, signs FastAPI admin headers server-side, and renders title/slug/status/published date/editor link.
  - Extended authenticated E2E to visit `/admin/blog`, assert `Blog posts` and `New draft`, then open editor and publish `test-post.md` content.
  - Fixed `BlogRepository(posts=[])` so an explicit empty test repository no longer falls back to default seed posts.
  - `python -m pytest backend/tests` → passed: 25 tests.
  - `cd frontend && npm run test && npm run typecheck && npm run lint && npm run build && npm run test:e2e` → passed; E2E `6 passed`.
  - `scripts/bin/harness-cli.exe story verify US-015` → passed the full configured verification command.
