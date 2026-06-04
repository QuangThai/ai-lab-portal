# US-057 Admin Review Affordances for Social Context

## Status

implemented

## Lane

normal

## Product Contract

Add social context display to the existing admin AI News review queue. Show
author metadata (handle, display name, verified status, follower count),
engagement metrics (likes, reposts, replies), risk flags, and source post URL
for social-sourced items. Non-social items remain unaffected.

## Relevant Product Docs

- `docs/stories/epics/E05-x-twitter/README.md`
- `docs/decisions/0009-x-twitter-data-contract.md`
- `docs/decisions/0010-x-twitter-moderation-policy.md`
- `backend/app/news_scoring.py`
- `frontend/app/admin/news-review/page.tsx`
- `frontend/app/admin/news-review/review-item-card-list.tsx`

## Acceptance Criteria

- `NewsReviewItem` includes a `social_metadata` JSON field carrying author
  handle, display name, verified status, follower count, engagement counts,
  risk flags, and source post URL (nullable, only for social-sourced items).
- `_extract_social_metadata()` generates the display-relevant JSON from the
  raw item payload during scoring.
- `upsert_scored()` stores the `social_metadata` on the review item.
- The admin review UI shows a social context panel when `social_metadata` is
  present, including: source label (X/Twitter), author info, engagement
  metrics, risk badges, and View post link.
- The review UI shows `author_credibility_score` and `social_engagement_score`
  when available in the score dimensions grid.
- Non-social items show no social section — backward compatible.
- DB migration adds `social_metadata` text column to `news_review_items`.
- Frontend typecheck and lint pass.

## Non-Goals

- No changes to the publish flow or review actions.
- No changes to non-social item display.
- No real provider API calls.

## Design Notes

- Social metadata is stored as a JSON text column on the review item to avoid
  extra DB joins during list queries. The data is extracted from the raw item's
  `raw_payload` during scoring.
- The frontend parses `social_metadata` and renders a collapsible context panel
  only when present. Items without social metadata render identically to before.
- Risk flags display as color-coded badges (`warning` for spam/bait, `info` for
  low credibility, `destructive` for drama/rumor).

## Validation

| Layer | Expected proof |
| --- | --- |
| Unit | `python -m pytest backend/tests/test_news_scoring_social.py` — 15 passed |
| Integration | Existing social/news tests — 42 passed combined |
| E2E | Not required; UI extension only, no new flows. |
| Platform | Not required. |
| Release | `cd frontend && npm run typecheck && npm run lint` — passed. |

## Harness Delta

- Added `social_metadata` field to `NewsReviewItem` model
- Added `social_metadata_json` parameter to `upsert_scored()` in all three repos
- Updated `_extract_social_metadata()` to generate display-relevant JSON
- Updated `_score_with_heuristics()` and `run_score_extracted_article()` to pass
  social metadata through
- DB migration `20260604_0022_social_metadata_column.py`
- Updated frontend `AdminNewsReviewItem` type with new fields
- Added `SocialContext`, `SocialBadge`, and `parseSocialMetadata` components
- Updated score dimensions grid to show social scores when available

## Evidence

- `python -m pytest backend/tests/test_news_scoring_social.py
  backend/tests/test_news_scoring.py backend/tests/test_news_social_x_ingest.py
  backend/tests/test_social_x.py backend/tests/test_news_sources.py` — 42 passed.
- `cd frontend && npm run typecheck` — passed.
- `cd frontend && npm run lint` — passed.
- All social display is backward-compatible; non-social items unchanged.
