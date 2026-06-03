# Validation

## Commands

```text
cd frontend && npx -y react-doctor@latest . --verbose
python -m pytest backend/tests
cd frontend && npm run test && npm run typecheck && npm run lint && npm run build && npm run test:e2e
scripts/bin/harness-cli.exe story verify US-020
```

## Acceptance Evidence

- 2026-06-02 US-020 shadcn admin CMS polish:
  - Initialized shadcn/ui in `frontend/` (`components.json`, `lib/utils.ts` with `cn`, Tailwind v4 imports).
  - Mapped editorial tokens from `theme.css` / style guide to shadcn CSS variables (`--background`, `--primary`, `--brand`, `--ring`, etc.).
  - Added primitives: `button`, `input`, `textarea`, `label`, `badge` (+ `success`), `card`, `separator`, `alert`.
  - Shared admin helpers: `admin-ui.ts`, `AdminCmsShell`, `AdminPageHeader`, `AdminBackLink`, `AdminStatusBadge`.
  - Refactored `/admin/login`, `/admin`, `/admin/blog`, editor routes, and `BlogEditor` to shadcn primitives.
  - Preserved semantic `h1` headings and E2E selectors (`Open editor`, `New draft`, `role=status`).
  - React Doctor: **92/100** (remaining warnings are mostly App Router/tooling noise).
  - `python -m pytest backend/tests` → 26 passed.
  - `cd frontend && npm run test && npm run typecheck && npm run lint && npm run build && npm run test:e2e` → passed; E2E **6 passed**.
  - `scripts/bin/harness-cli.exe story verify US-020` → pass.
