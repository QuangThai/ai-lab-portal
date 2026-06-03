# Validation

## Proof Strategy

Prove that the rich editor UI renders, remains protected by admin auth, and keeps the existing API/backend proof green. If API wiring is included, prove save/publish actions through tests.

## Test Plan

| Layer | Cases |
| --- | --- |
| Unit | Editor adapter serializes content safely enough for the backend payload. |
| Integration | Existing admin blog API tests continue to pass. |
| E2E | Unauthenticated admin editor access redirects to login; editor page renders toolbar/form for authenticated or test-safe route if auth fixture exists. |
| Platform | Next.js typecheck/lint/build pass with Tiptap client component. |
| Accessibility | Form controls have labels and toolbar buttons have accessible names. |
| Logs/Audit | No cookies, signed headers, passwords, or raw secrets are logged. |

## Fixtures

- Deterministic draft post/editor content.
- Existing admin identity boundary fixtures if API actions are tested.

## Commands

```text
python -m pytest backend/tests
cd frontend && npm run test && npm run typecheck && npm run lint && npm run build && npm run test:e2e
```

## Acceptance Evidence

- 2026-06-02 US-007 rich admin blog editor UI:
  - Researched Tiptap, Plate, and Lexical using Context7 docs.
  - Chose Tiptap because it is headless, Next.js App Router compatible with `immediatelyRender: false`, and easy to style with shadcn-style controls.
  - Installed `@tiptap/react` and `@tiptap/starter-kit`.
  - `python -m pytest backend/tests` → passed: 23 tests.
  - `cd frontend && npm run test && npm run typecheck && npm run lint && npm run build && npm run test:e2e` → passed.
  - E2E covers unauthenticated `/admin/blog/editor` redirect to `/admin/login`.
  - Next.js build includes dynamic `/admin/blog/editor` route.
  - `npm install` reported 2 moderate advisories; not force-fixed because npm indicated breaking changes and this story is not dependency security hardening.
  - `scripts/bin/harness-cli.exe story verify US-007` → passed the full configured verification command.
