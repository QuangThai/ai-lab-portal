# Validation Report: {{STORY_ID}}

> Template for story validation reports.
> Copy this file to `docs/validation/{{STORY_ID}}-report.md` after verification.

## Summary

- **Date:** {{DATE}}
- **Verifier:** {{AGENT_NAME}}
- **Result:** {{PASSED / FAILED / PARTIAL}}

## Layer Results

| Layer | Tests | Passed | Failed | Notes |
|-------|-------|--------|--------|-------|
| Unit  | {{N}}  | {{N}}  | {{N}}  | {{e.g., pytest backend/tests/test_*.py}} |
| Integration | {{N}} | {{N}} | {{N}} | {{e.g., pytest backend/tests/test_*integration*.py}} |
| E2E   | {{N}}  | {{N}}  | {{N}}  | {{e.g., Playwright tests}} |
| Platform | {{N}} | {{N}} | {{N}} | {{e.g., Docker compose up}} |

## Commands Used

```bash
{{verification command 1}}
{{verification command 2}}
```

## Details

### Unit Tests

```
{{paste output summary here}}
```

### Integration Tests

```
{{paste output summary here}}
```

### E2E Tests

```
{{paste output summary here}}
```

## Evidence Notes

- {{Any special conditions: e.g., fake provider used}}
- {{Known limitations: e.g., no CI run}}
- {{Proof flags: unit=yes, integration=yes, e2e=yes, platform=n/a}}

## Decisions

- {{Any architectural decisions made during verification}}

## Follow-up

- [ ] {{Any items to address later}}
