# Validation

## Commands

```text
python -m pytest backend/tests
cd frontend && npm run test && npm run typecheck && npm run lint && npm run build && npm run test:e2e
```

## Acceptance Evidence

- 2026-06-02 US-019 CMS action feedback and pending states:
  - Added reusable `PendingSubmitButton` using `useFormStatus()`.
  - Editor Save/Publish buttons now show `Saving draft…` / `Publishing…`, disabled state, and `aria-busy` while submitting.
  - Editor status panel includes clearer server-action guidance.
  - Admin list Publish/Unpublish buttons now show `Publishing…` / `Unpublishing…`, disabled state, and `aria-busy` while submitting.
  - No third-party toast dependency was added.
  - `python -m pytest backend/tests` → passed: 26 tests.
  - `cd frontend && npm run test && npm run typecheck && npm run lint && npm run build && npm run test:e2e` → passed; E2E `6 passed`.
  - `scripts/bin/harness-cli.exe story verify US-019` → passed the full configured verification command.
