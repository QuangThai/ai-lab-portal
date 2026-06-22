# Verification Protocol

This protocol defines how harness verification works across all maturity
levels. It covers story-level verification, proof-column management, batch
verification, and validation reporting.

## Overview

Verification ensures that implemented stories meet their validation expectations
before they are marked complete. The harness supports verification at multiple
layers:

| Layer | Tool | Speed | What it checks |
|-------|------|-------|---------------|
| **Quick** | `scripts/verify_all_stories.py` (default) | <5s | Proof flags in matrix |
| **Full** | `scripts/bin/harness-cli story verify <id>` | varies | Configurable verification commands |
| **Full batch** | `scripts/verify_all_stories.py --full` | slow | All story verify commands |
| **Benchmark** | `python scripts/harness_benchmark.py` | <60s | Overall harness health |

## Story-Level Verification

Each story can have a `verify_command` — a shell command that proves the story's
validation expectations. This is set when creating or updating a story:

```bash
scripts/bin/harness-cli story update --id US-001 --verify "cd frontend && npm run typecheck"
```

When `story verify <id>` runs:

1. The CLI looks up the story's `verify_command`.
2. If set, it executes the command.
3. If the command exits with code 0, verification passes.
4. If no command is set, the CLI checks proof flags only.
5. The result is stored in `story.last_verified_result`.
6. The `trace` command warns when linking to a story whose verification has not
   passed.

### Adding Verification to a Story

1. Run feature intake and create the story.
2. After implementation, set the verify command using:
   ```bash
   scripts/bin/harness-cli story update --id <ID> --verify "<command>"
   ```
3. Run verification:
   ```bash
   scripts/bin/harness-cli story verify <ID>
   ```
4. Record proof flags:
   ```bash
   scripts/bin/harness-cli story update --id <ID> --unit 1 --integration 1 --e2e 1 --platform 0
   ```

## Proof Columns

The test matrix tracks four proof layers:

| Column | Meaning | Source |
|--------|---------|--------|
| **unit** | Unit tests pass | `pytest backend/tests/test_*.py` |
| **integration** | Integration tests pass | `pytest backend/tests/test_*integration*.py` |
| **e2e** | Playwright E2E tests pass | `npm run test:e2e` from `frontend/` |
| **platform** | Platform/deployment works | Manual or CI check |

Proof values:

| Value | Meaning |
|-------|---------|
| `yes` | Verified and passing |
| `no` | Not applicable for this story (e.g., frontend-only story has no unit tests) |
| `n/a` | Platform-level proof not yet measured |

When verifying, all four values must be `yes` or `n/a` for the story to pass
quick verification.

## Batch Verification

Run batch verification across all stories:

```bash
# Quick mode — checks proof flags only
python scripts/verify_all_stories.py

# Full mode — runs story verify commands
python scripts/verify_all_stories.py --full
```

Batch verification reports:
- Total stories
- Pass/fail per story
- Summary counts

## Verification Commands Reference

Common verification commands:

```bash
# Backend unit tests
cd backend && python -m pytest -q --tb=short

# Backend integration tests
cd backend && python -m pytest -q tests/test_*integration*.py --tb=short

# Backend full suite
cd backend && python -m pytest -q --tb=short -x

# Frontend typecheck
cd frontend && npm run typecheck

# Frontend build
cd frontend && npm run build

# Frontend E2E (requires Docker)
cd frontend && CI=1 npm run test:e2e

# Full frontend quality
cd frontend && npm run quality:full

# E2E flakiness check
cd frontend && npm run quality:e2e-flakiness
```

## Validation Reports

After verification, record a validation report in the story's evidence column
or in a separate file under `docs/validation/`. Each report should include:

1. **Verification date**
2. **Layer results** (unit, integration, e2e, platform)
3. **Test counts** (passed, failed, total)
4. **Any failures** with root cause
5. **Verification command used**
6. **Exit code**

### Example Validation Report

```
# Validation Report: US-107

## Summary
- Date: 2026-06-22
- Verifier: pi (via story verify)
- Result: PASSED

## Layer Results
| Layer | Tests | Passed | Failed |
|-------|-------|--------|--------|
| Unit  | 11    | 11     | 0 |
| Integration | 5 | 5 | 0 |
| E2E   | 1     | 1      | 0 |
| Platform | n/a | — | — |

## Commands Used
- Unit: `pytest backend/tests/test_content_repurpose.py -q`
- Integration: `pytest backend/tests/test_content_repurpose_integration.py -q`
- E2E: `npx playwright test --grep "US-107"`

## Notes
- All tests pass. No regressions detected.
- Uses fake provider (no LLM calls).
```

## Updating Proof Columns

After verification, update the story's proof flags:

```bash
# Manual update
scripts/bin/harness-cli story update --id US-107 --unit 1 --integration 1 --e2e 1 --platform 0

# Via batch script
python scripts/verify_all_stories.py
```

Proof flags should be updated when:
- A story is first verified
- New tests are added for a story
- A regression is fixed and tests pass again
- A story's scope changes (e.g., frontend-only → full-stack)
