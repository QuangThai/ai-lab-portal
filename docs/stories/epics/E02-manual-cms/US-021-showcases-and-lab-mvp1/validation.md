# Validation

## Commands

```text
python -m pytest backend/tests
cd frontend && npm run test && npm run typecheck && npm run lint && npm run build && npm run test:e2e
scripts/bin/harness-cli.exe story verify US-021
```

## Acceptance Evidence

- 2026-06-02 US-021 showcases and lab MVP1:
  - Added `showcases` migration, repository module, admin/public FastAPI routes, and backend tests.
  - Added public `/showcases`, `/showcases/[slug]`, `/lab`, and admin `/admin/showcases` CMS (list, editor, edit).
  - Extended `AdminCmsShell` navigation; dashboard links to showcases.
  - Playwright E2E runs `alembic upgrade head` before backend start so migration `20260602_0005` applies in CI/local E2E.
  - `python -m pytest backend/tests` → 32 passed.
  - `cd frontend && npm run test && npm run typecheck && npm run lint && npm run build && npm run test:e2e` → passed; E2E **7 passed**.
  - `scripts/bin/harness-cli.exe story verify US-021` → pass.
