# Validation

## Commands

```text
python -m pytest backend/tests
cd frontend && npm run test && npm run typecheck && npm run lint && npm run build && npm run test:e2e
scripts/bin/harness-cli.exe story verify US-022
```

## Acceptance Evidence

- 2026-06-02 US-022 MVP 1 public polish:
  - Added `PublicSiteShell` with nav to `/lab`, `/showcases`, `/blog`, and admin link.
  - Added `public-ui.ts` token-backed classes and `createPublicMetadata` for canonical + OpenGraph.
  - Migrated `/`, `/blog`, `/showcases`, `/lab` to shared shell and shadcn theme tokens.
  - Homepage reflects live MVP 1 capabilities with entry-point cards and CTAs.
  - Updated `docs/TEST_MATRIX.md` with MVP 1 story rows.
  - E2E home test updated for new navigation and headings.
  - `python -m pytest backend/tests` → 32 passed.
  - `cd frontend && npm run test && npm run typecheck && npm run lint && npm run build && npm run test:e2e` → passed; E2E **7 passed**.
  - `scripts/bin/harness-cli.exe story verify US-022` → pass.
