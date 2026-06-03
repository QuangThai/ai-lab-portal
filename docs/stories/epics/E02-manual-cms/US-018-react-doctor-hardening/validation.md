# Validation

## Commands

```text
cd frontend && npx -y react-doctor@latest . --verbose
python -m pytest backend/tests
cd frontend && npm run test && npm run typecheck && npm run lint && npm run build && npm run test:e2e
```

## Acceptance Evidence

- 2026-06-02 US-018 React Doctor frontend hardening:
  - Read and applied `vercel-react-best-practices`, `frontend-design`, `react-doctor`, and `design-taste-frontend` guidance.
  - Ran `cd frontend && npx -y react-doctor@latest . --verbose`; initial score was 89/100.
  - Fixed actionable issues: metadata for public pages, internal anchor to `Link`, login button label, trusted-origin parsing, server action auth placement, and module-level action state warning.
  - Re-ran React Doctor: score improved to 94/100.
  - Remaining React Doctor errors are false positives for server action auth wrappers: exported actions now call `requireSession()` as their first statement, but the tool does not recognize the helper wrapper. Remaining unused-file/dependency warnings are also likely App Router/tooling false positives.
  - `python -m pytest backend/tests` → passed: 26 tests.
  - `cd frontend && npm run test && npm run typecheck && npm run lint && npm run build && npm run test:e2e` → passed; E2E `6 passed`.
  - `scripts/bin/harness-cli.exe story verify US-018` → passed the full configured verification command.
