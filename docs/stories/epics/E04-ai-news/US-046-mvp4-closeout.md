# US-046 MVP4 User-Submitted Links Closeout

## Status

implemented

## Lane

tiny

## Product Contract

Close MVP 4 (user-submitted links) with updated roadmap status and combined
verification for US-044–US-045.

## Acceptance Criteria

- `docs/product/mvp-roadmap.md` marks MVP 4 **Implemented** (US-044–US-045).
- Epic E04 user-submitted links marked implemented in backlog.
- Combined submission tests pass.
- Harness story verify passes.

## Validation

```bash
python -m pytest backend/tests/test_news_submitted_links.py
scripts/bin/harness-cli story verify US-046
```

## Evidence

- 2026-06-03: `python -m pytest backend/tests/test_news_submitted_links.py` → 5 passed.
- 2026-06-03: `scripts/bin/harness-cli story verify US-046` → pass.

## Deferred (post-MVP4)

- AI classification output on submissions.
- Dedicated admin review UI for submitted links.
