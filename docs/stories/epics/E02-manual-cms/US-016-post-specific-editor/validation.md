# Validation

## Proof Strategy

Run full verification and authenticated E2E that opens an existing post-specific editor from the admin list.

## Commands

```text
python -m pytest backend/tests
cd frontend && npm run test && npm run typecheck && npm run lint && npm run build && npm run test:e2e
```

## Acceptance Evidence

- 2026-06-02 US-016 post-specific admin editor route:
  - Added `GET /admin/blog-posts/{id}` requiring signed admin identity.
  - Added repository `get_by_id()` for in-memory and Postgres implementations.
  - Added `/admin/blog/[id]/edit` protected Next.js route that fetches the existing post and pre-fills title, slug, excerpt, author, content, and post id.
  - Updated admin blog list row action to link to `/admin/blog/{id}/edit`.
  - Extended authenticated E2E to open an existing post-specific editor from `/admin/blog`, then return to create/publish `test-post.md` content.
  - `python -m pytest backend/tests` → passed: 26 tests.
  - `cd frontend && npm run test && npm run typecheck && npm run lint && npm run build && npm run test:e2e` → passed; E2E `6 passed`.
  - `scripts/bin/harness-cli.exe story verify US-016` → passed the full configured verification command.
