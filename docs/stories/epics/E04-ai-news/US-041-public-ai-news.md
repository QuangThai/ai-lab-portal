# US-041 Public AI News Feed

## Status

implemented

## Product Contract

Approved review items can be published to the public `/ai-news` feed with stable
slugs. Public API exposes list and detail; unpublish removes items from the feed.

## Acceptance Criteria

- Migration `20260603_0018` adds `slug` and `published_at` on `news_review_items`.
- Admin `POST /admin/news/review-items/{id}/publish|unpublish`.
- Public `GET /public/ai-news` and `GET /public/ai-news/{slug}`.
- Frontend pages `/ai-news` and `/ai-news/[slug]`.
- Tests in `backend/tests/test_news_publish.py`.

## Validation

```bash
python -m pytest backend/tests/test_news_publish.py
scripts/bin/harness-cli story verify US-041
```

## Evidence

- 2026-06-03: `python -m pytest backend/tests/test_news_publish.py` → 3 passed.
- 2026-06-03: `scripts/bin/harness-cli story verify US-041` → pass.
