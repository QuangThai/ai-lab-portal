# Validation

## Commands

```text
python -m pytest backend/tests
cd frontend && npm run test && npm run typecheck && npm run lint && npm run build && npm run test:e2e
```

## Acceptance Evidence

- 2026-06-02 US-017 admin list publish actions:
  - Added Next.js server actions for publish/unpublish from `/admin/blog`.
  - Actions check Better Auth session, sign FastAPI admin headers server-side, call existing FastAPI mutation endpoints, and revalidate `/admin/blog` and `/blog`.
  - Admin list rows now show `Publish` for drafts and `Unpublish` for published posts.
  - Authenticated E2E publishes `test-post.md`, verifies public visibility, unpublishes from admin list, and verifies the post no longer appears publicly.
  - `python -m pytest backend/tests` → passed: 26 tests.
  - `cd frontend && npm run test && npm run typecheck && npm run lint && npm run build && npm run test:e2e` → passed; E2E `6 passed`.
  - `scripts/bin/harness-cli.exe story verify US-017` → passed the full configured verification command.
