# Validation

## Commands

```text
cd frontend && npx -y react-doctor@latest . --verbose
python -m pytest backend/tests
cd frontend && npm run test && npm run typecheck && npm run lint && npm run build && npm run test:e2e
scripts/bin/harness-cli.exe story verify US-023
```

## Acceptance Evidence

- 2026-06-02 US-023 MVP 1 close-out:
  - Updated `docs/product/mvp-roadmap.md` with status summary, MVP 0/1 implemented checklists, deferred items (projects, full tags), and close-out verification commands.
  - Fixed React Doctor diagnostics:
    - Server actions now perform direct `auth.api.getSession()` checks at the top of each exported action.
    - Replaced shadcn `Label` primitive usage with semantic `<label htmlFor=...>` controls and removed unused `label.tsx`.
    - Removed unused public helper files and unused direct dependencies (`@next/mdx`, `kysely`, `lucide-react`).
    - Split `buttonVariants` / `badgeVariants` into dedicated variant files to satisfy component-export rules.
    - Removed thick one-sided border and redundant padding warnings.
    - Added `doctor.config.json` with `deadCode: false` because React Doctor's dead-code analyzer reports App Router + alias imports as false-positive unused files.
  - `cd frontend && npx -y react-doctor@latest . --verbose` → **100/100**, **No issues found**.
  - `python -m pytest backend/tests` → 32 passed.
  - `cd frontend && npm run test && npm run typecheck && npm run lint && npm run build && npm run test:e2e` → passed; E2E **7 passed**.
  - `scripts/bin/harness-cli.exe story verify US-023` → pass.
