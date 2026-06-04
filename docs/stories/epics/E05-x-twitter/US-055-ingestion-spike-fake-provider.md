# US-055 X/Twitter Ingestion Spike (Fake Provider)

## Status

implemented

## Lane

normal

## Product Contract

Add an ingestion path that connects the FakeXTwitterProvider and social link
filter to the existing AI News pipeline. All ingestion uses fake provider
fixtures — no real Apify, Firecrawl, or X/Twitter provider calls.

## Relevant Product Docs

- `docs/stories/epics/E05-x-twitter/README.md`
- `docs/decisions/0008-x-twitter-provider-strategy.md`
- `docs/decisions/0009-x-twitter-data-contract.md`
- `docs/decisions/0010-x-twitter-moderation-policy.md`
- `backend/app/social_x.py` (US-053/US-054)
- `backend/app/news_social_x_ingest.py`

## Acceptance Criteria

- `NewsSourceType` includes `"social_x"` as a valid type.
- A seed `social_x` news source exists (disabled by default).
- `run_social_x_ingest()` accepts a source ID, uses `FakeXTwitterProvider` to
  fetch posts, runs `filter_social_link_candidate()` on each, and stores
  accepted URLs as raw items in the existing pipeline.
- `run_due_social_x_sources()` crawls all due social_x sources.
- Celery tasks `news.ingest_social_x_source` and
  `news.ingest_due_social_x_sources` exist.
- All ingestion produces deterministic, repeatable results with fake fixtures.
- No real provider API calls are made.
- 9 tests cover: basic acceptance, nonexistent/different/disabled sources,
  last_crawled update, custom provider, due-source crawl, skip non-social
  sources, and skip not-yet-due sources.

## Non-Goals

- No real provider calls.
- No new database tables (reuses news_raw_items).
- No frontend/admin UI changes.
- No real Apify budget or terms approval.

## Design Notes

- The `url_or_identifier` field on the NewsSource stores the social handle
  (e.g., `@OpenAI`).
- Each accepted post URL creates a separate `ParsedFeedItem` in the raw items
  table, which then flows through the existing extraction → dedup → scoring →
  review pipeline.
- A `SocialPostSourceScope` is derived from the NewsSource config for each
  crawl run.
- The `content_hash` for raw items uses a unique-per-item strategy since fake
  provider output is deterministic per run.

## Validation

| Layer | Expected proof |
| --- | --- |
| Unit | `python -m pytest backend/tests/test_news_social_x_ingest.py` — 9 passed |
| Integration | `python -m pytest backend/tests/test_social_x.py` — 10 passed (regression) |
| E2E | Not required; no frontend change. |
| Platform | Not required. |
| Release | `git diff --check` clean. |

## Harness Delta

- Added `backend/app/news_social_x_ingest.py`
- Added `backend/tests/test_news_social_x_ingest.py`
- Added Celery tasks in `backend/app/tasks.py`
- Extended `NewsSourceType` in `backend/app/news_sources.py`
- Added seed `social_x` source in `backend/app/news_sources.py`

## Evidence

- `python -m pytest backend/tests/test_news_social_x_ingest.py` — 9 passed.
- `python -m pytest backend/tests/test_social_x.py` — 10 passed (regression).
- `git diff --check` — passed.
- All ingestion uses fake provider only; no real provider calls.
