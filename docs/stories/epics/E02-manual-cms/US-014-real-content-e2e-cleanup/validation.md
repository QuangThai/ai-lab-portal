# Validation

## Proof Strategy

Run full verification. E2E should publish content derived from `test-post.md`, assert it appears on `/blog`, and clean up E2E DB rows.

## Commands

```text
python -m pytest backend/tests
cd frontend && npm run test && npm run typecheck && npm run lint && npm run build && npm run test:e2e
```

## Acceptance Evidence

- 2026-06-02 US-014 real content E2E and CMS cleanup:
  - E2E reads `test-post.md` from repo root and publishes it as `Pi and Codex Agent Workflow Tips`.
  - The editor fills title, slug, excerpt, and Tiptap content from the real markdown file.
  - E2E verifies the public detail contains Pi package content (`pi-subagents`) and Codex command content (`codex feature list`).
  - Added Playwright-side Postgres cleanup for the E2E blog post, audit rows, Better Auth sessions/accounts/users.
  - No production cleanup endpoint or auth bypass was added.
  - `python -m pytest backend/tests` → passed: 23 tests.
  - `cd frontend && npm run test && npm run typecheck && npm run lint && npm run build && npm run test:e2e` → passed; E2E `6 passed`.
  - `scripts/bin/harness-cli.exe story verify US-014` → passed the full configured verification command.
