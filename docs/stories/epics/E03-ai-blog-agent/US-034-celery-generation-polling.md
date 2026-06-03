# US-034 Celery Generation Job Polling

## Status

implemented

## Product Contract

Queued Celery generations persist `blog_generation_jobs` with status transitions. Admin UI polls `GET /admin/blog-ideas/generation-jobs/{task_id}` until completed/failed.

## Evidence

- `backend/app/generation_jobs.py`, `frontend/app/admin/blog-ideas/generation-job-poller.tsx`
- `backend/tests/test_blog_observability.py`
