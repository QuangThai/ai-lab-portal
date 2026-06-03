# US-036 News Source Registry

## Status

implemented

## Product Contract

Admins can list, create, enable/disable, and configure crawl sources (RSS, GitHub, website) for AI News.

## Evidence

- `backend/app/news_sources.py`, migration `20260603_0013`
- Admin UI `/admin/news-sources`
- `backend/tests/test_news_sources.py`
