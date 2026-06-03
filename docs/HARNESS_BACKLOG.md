# Harness Backlog

Use this file when an agent discovers a missing harness capability but should
not change the operating model immediately. Operational records live in
`harness.db`; sync with `scripts/bin/harness-cli query backlog`.

## Template

```md
## Missing Harness Capability

### Title

Short name.

### Discovered While

Task or story that exposed the gap.

### Current Pain

What was hard, repeated, ambiguous, or unsafe?

### Suggested Improvement

What should be added or changed?

### Risk

Tiny, normal, or high-risk.

CLI value: `--risk tiny`, `--risk normal`, or `--risk high-risk`.

### Status

proposed | accepted | implemented | rejected
```

## Items

### #1 — Initialize git repository for harness verification

- **Status:** implemented
- **Risk:** normal
- **Discovered while:** Repeated trace friction review (traces 1–39)
- **Pain:** Workspace was not a git checkout; git status and diff review unavailable.
- **Outcome:** `git init` completed; future tasks can use git for proof.

### #2 — Align root `.env` database and Redis ports with compose

- **Status:** implemented
- **Risk:** tiny
- **Discovered while:** US-009, US-013, US-014 trace friction
- **Pain:** Root `.env` used `5432`/`6379` while compose exposes `15432`/`16379`.
- **Outcome:** Root `.env` aligned with `.env.example` host ports.

### #3 — Restore or replace `ui-ux-pro-max` skill symlink

- **Status:** implemented
- **Risk:** tiny
- **Discovered while:** Landing redesign (traces 15, 18)
- **Pain:** Skill path was a broken symlink; agents used `frontend-design` / `impeccable` fallback.
- **Outcome:** Skill files restored at `.agents/skills/ui-ux-pro-max/`; all symlinks resolve.

### #4 — Local dev quickstart for ports and `DATABASE_URL`

- **Status:** implemented
- **Risk:** normal
- **Discovered while:** Foundation and CMS E2E traces
- **Pain:** Host vs Docker ports and env files scattered across README and `.env.example`.
- **Outcome:** Added `docs/local-dev.md` and linked from `docs/README.md`.

### #5 — Friction deduplication guideline for traces

- **Status:** implemented
- **Risk:** tiny
- **Discovered while:** Harness maturity H3 friction-to-backlog review
- **Pain:** Same environment friction copied into dozens of traces.
- **Outcome:** Recurring-friction rules added to `docs/TRACE_SPEC.md`.

### #6 — Add husky/lint-staged pre-commit hooks for frontend typecheck and build

- **Status:** implemented
- **Risk:** tiny
- **Discovered while:** UI/UX improvement session
- **Pain:** Devs must manually run typecheck and build after every frontend change; easy to forget.
- **Outcome:** Repo-root `.husky/pre-commit` runs `npm run quality:precommit` in `frontend/` (lint-staged, typecheck, build). `npm install` in `frontend/` sets `core.hooksPath` via `scripts/setup-git-hooks.mjs`.

### #7 — Add dark mode toggle button to admin CMS shell sidebar

- **Status:** implemented
- **Risk:** tiny
- **Discovered while:** UI/UX improvement session
- **Pain:** CSS dark mode variables are defined but no UI to switch; users on dark OS get no toggle.
- **Outcome:** `next-themes` provider plus light/dark toggle in `admin-cms-shell` (desktop sidebar and mobile header).

### #8 — Add trace quality audit command

- **Status:** implemented
- **Risk:** tiny
- **Discovered while:** Harness friction/trace audit (trace 60)
- **Pain:** Incomplete traces required ad hoc SQL.
- **Outcome:** `python scripts/trace_quality.py` audits core trace fields; documented in `scripts/README.md`. Native Rust CLI integration remains optional later.
