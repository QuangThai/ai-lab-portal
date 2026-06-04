# US-054 AI Social Link Filter Contract

## Status

implemented

## Lane

normal

## Product Contract

Define the structured pre-extraction social filter output for normalized X/Twitter posts. This slice remains fake-first and deterministic: no real Apify, Firecrawl, X/Twitter, or LLM provider calls.

## Acceptance Criteria

- The filter accepts `NormalizedSocialPost` input from US-053.
- The output includes `should_ingest`, `reason`, `topic`, `priority`, `risk_flags`, `urls_to_extract`, and `requires_human_review`.
- Accepted social posts always require human review.
- `urls_to_extract` only comes from normalized post URL entities.
- Low-signal posts without extractable URLs are rejected.
- Spam/engagement-bait posts are rejected and flagged.
- Tests cover accepted, rejected, and risky decisions.

## Design Notes

- Commands: none.
- Queries: none.
- API: no public/admin API change.
- Tables: no migration.
- Domain rules: filter is a local deterministic stand-in for the future AI social filter contract.
- UI surfaces: none.

## Validation

| Layer | Expected proof |
| --- | --- |
| Unit | `python -m pytest backend/tests/test_social_x.py` |
| Integration | Run related AI News crawl/source tests before closeout/commit. |
| E2E | Not required; no frontend change. |
| Platform | Not required. |
| Release | `git diff --check` clean. |

## Evidence

- `python -m pytest backend/tests/test_social_x.py` — 10 passed.
