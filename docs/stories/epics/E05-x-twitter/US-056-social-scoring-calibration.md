# US-056 Social Item Scoring Calibration

## Status

implemented

## Lane

normal

## Product Contract

Tune the existing AI News heuristic scoring dimensions for X/Twitter social
signals. Add `author_credibility_score` and `social_engagement_score` to the
scoring model, handle nullable engagement metrics, and incorporate social
risk flags into spam scoring.

## Relevant Product Docs

- `docs/stories/epics/E05-x-twitter/README.md`
- `docs/decisions/0009-x-twitter-data-contract.md`
- `docs/decisions/0010-x-twitter-moderation-policy.md`
- `backend/app/news_scoring.py`
- `backend/app/social_x.py`

## Acceptance Criteria

- `ScoreDimensions` model includes `author_credibility_score` and
  `social_engagement_score` as optional fields (None when no social data).
- `NewsReviewItem` model includes the same two fields for persistence.
- `compute_heuristic_scores()` accepts an optional `raw_item_payload` parameter
  and extracts social metadata (engagement, author credibility, risk flags).
- Engagement score uses actual social engagement metrics (likes, reposts,
  replies) when available, with nullable handling.
- Author credibility score is computed from verified status and follower count.
- Social spam risk flags (e.g., `spam_or_engagement_bait`) boost the spam score.
- Non-social sources (RSS, website, etc.) get None for social scores and
  preserve existing behavior.
- DB migration adds `author_credibility_score` and `social_engagement_score`
  columns to `news_review_items`.
- 15 tests cover: metadata extraction edge cases, engagement normalization,
  author credibility calibration, spam boost, default values for non-social
  sources, ScoreDimensions model validation, and upsert pipeline.

## Non-Goals

- No LLM-based social scoring (remains heuristic-based for MVP 5).
- No admin UI changes for social scoring display (US-057).
- No real provider API calls.

## Design Notes

- Social metadata is extracted from the raw item's `raw_payload` dict (populated
  during social ingestion in US-055). In the in-memory repo, `raw_payload` is
  not available, so social scores remain None. In the Postgres repo, the DB
  column carries the payload.
- Engagement normalization: sum of likes + reposts + replies, capped at 1,000 →
  score 0.0–1.0.
- Author credibility baseline: 0.5. Add 0.25 for verified, subtract 0.1 for
  unverified. Add 0.2 for 100k+ followers, 0.1 for 10k+, subtract 0.1 for
  < 1k followers.
- Existing `SCORER_VERSION` kept as `heuristic_v1`; version bumps deferred until
  a formal social scorer version is needed.

## Validation

| Layer | Expected proof |
| --- | --- |
| Unit | `python -m pytest backend/tests/test_news_scoring_social.py` — 15 passed |
| Integration | `python -m pytest backend/tests/test_news_scoring.py` — 6 passed (regression) |
| E2E | Not required; no frontend change. |
| Platform | Not required. |
| Release | `git diff --check` clean. |

## Harness Delta

- Added `author_credibility_score` and `social_engagement_score` to `ScoreDimensions`
- Added `_extract_social_metadata()` function in `news_scoring.py`
- Updated `compute_heuristic_scores()` to accept `raw_item_payload` parameter
- Updated `_score_with_heuristics()` to forward raw_payload
- Updated `run_score_extracted_article()` to extract raw_payload from raw items
- Updated both `InMemoryNewsReviewRepository` and `PostgresNewsReviewRepository`
  `upsert_scored()` to include the new fields
- DB migration `20260604_0021_social_scoring_columns.py`
- 15 new tests in `tests/test_news_scoring_social.py`

## Evidence

- `python -m pytest backend/tests/test_news_scoring_social.py` — 15 passed.
- `python -m pytest backend/tests/test_news_scoring.py` — 6 passed (regression).
- `git diff --check` — passed.
- All social scoring remains heuristic; no real provider calls.
