# US-033 AI Run Metadata Persistence

## Status

implemented

## Product Contract

Each important LLM call for a blog idea records provider, model, prompt name/version, inputs, outputs, token usage, and latency in `ai_runs`.

## Evidence

- `backend/app/ai_runs.py`, `backend/app/llm/recording.py`, migration `20260603_0012`
- `backend/tests/test_blog_observability.py`
