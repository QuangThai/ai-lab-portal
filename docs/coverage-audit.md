# Backend Test Coverage Audit

Generated: 2026-06-07
Overall coverage: **65%** (2244 of 6440 statements missing)

---

## Priority Matrix: High-Impact Modules (< 50% coverage)

These are the core pipeline paths where low coverage represents real production risk.

---

### 1. `streaming_routes.py` — 23% (99/129 missing)

**What it does:** FastAPI SSE streaming endpoints for all blog pipeline stages (outline, draft, technical review, marketing). Each endpoint validates the idea state, builds LLM inputs, calls `stream_generate()`, saves the result, and emits a `saved` SSE event.

**Uncovered paths:**
- All 4 streaming endpoint handlers: `generate_outline_stream`, `generate_draft_stream`, `generate_review_stream`, `generate_marketing_stream` (lines 59-269)
- Status validation: each endpoint checks idea state (approved, outline approved, draft approved) and returns 400 on failure
- `event_stream()` inner generators: stream iteration, result JSON buffering, `model_validate()` parsing
- Save-and-emit logic: `repository.set_outline()`, `repository.set_draft()`, `repository.set_technical_review()`, `repository.set_marketing_metadata()` with error handling
- The `_streaming_response()` helper and `_make_identity_dep()` factory

**Tests needed:**
- Integration tests with `TestClient` for each of the 4 streaming endpoints — mock `stream_generate` to yield controlled SSE events, verify SSE response stream parsing, verify repository state changes
- Error cases: idea not found (404), wrong status (400), save failure, event stream error
- Auth tests: missing/invalid admin identity headers (401)
- Fixtures: pre-seeded `BlogIdea` in various states (approved outline, approved draft, etc.), mocked `stream_generate` async generator

**Priority: HIGH** — These are the live user-facing endpoints. Any bug in streaming corrupts the admin UI experience. No tests exercise the core SSE save flow at all.

---

### 2. `tasks.py` — 22% (204/262 missing)

**What it does:** All Celery background tasks for the blog pipeline (idea generation, outline, draft, technical review, marketing) and news pipeline (RSS crawl, extraction, scoring, social X ingest, GitHub ingest). Scheduled publishing task.

**Uncovered paths:**
- All blog generation tasks: `generate_blog_idea_task`, `generate_blog_outline_task`, `generate_blog_draft_task`, `generate_technical_review_task`, `generate_marketing_metadata_task` (lines 79-569)
- `_generate_blog_draft()` sectional expansion logic with retry loop (lines 104-189)
- `_generate_blog_draft_sectional()` per-section expansion with `prior_sections_summary`
- `publish_scheduled_posts_task()` - scheduled publishing logic with datetime comparison
- All news pipeline tasks: `crawl_rss_source_task`, `extract_raw_item_task`, `score_extracted_article_task`, `process_submitted_link_task`
- Social/GitHub ingest tasks: `ingest_social_x_source_task`, `fetch_github_source_task`
- `_finish_job()` and `_idea_create_from_llm()` helpers
- `crawl_due_rss_sources_task`, `extract_pending_raw_items_task`, `score_pending_extractions_task`, `ingest_due_social_x_sources_task`, `fetch_due_github_sources_task`

**Tests needed:**
- Unit tests using Celery `task_always_eager=True` for each blog generation task with `FakeLLMService`
- Draft generation: test sectional vs monolithic paths, retry logic when draft too short, word-count validation
- Task error handling: task retries on `LLMGenerationError`, `_finish_job` recording failure in `GenerationJobRepository`
- Published scheduled posts: seed ideas with `scheduled_at` in past/future
- News pipeline tasks: eager mode tests with in-memory repositories
- Fixtures: `BlogIdeaRepository` seeded with ideas at each pipeline stage, `FakeLLMService` responses, `GenerationJobRepository`, `AiRunRepository`

**Priority: HIGH** — These tasks perform all LLM calls and pipeline orchestration. Draft generation has complex retry logic and sectional expansion with multiple code paths depending on word count thresholds. Any regression here breaks the entire content pipeline.

---

### 3. `llm/streaming.py` — 33% (56/84 missing)

**What it does:** Async streaming SSE generator (`stream_generate()`). Uses Agents SDK `Runner.run_streamed()` to stream tokens via SSE events. Handles agent construction, stream event iteration, output validation, and recording to `AiRunRepository`.

**Uncovered paths:**
- `stream_generate()` async generator: full stream event loop (lines 95-205)
- Agent construction path (when no pre-built agent provided): `PROMPT_REGISTRY` lookup, `Agent()` instantiation, `Runner.run_streamed()` call
- Stream event handling: `ResponseTextDeltaEvent`, `ResponseTextDoneEvent`, `ResponseCompletedEvent`, `ResponseErrorEvent`, `ResponseFailedEvent`
- Type-check on final output (`isinstance(parsed, output_schema)`)
- Recording path: `recorder.record_completed()` with token usage extraction and `hooks.total_ms`
- Error handling: `LLMGenerationError`, generic `Exception`, `set_tracing_disabled`
- Pre-built agent branch (agent is not None)

**Tests needed:**
- Unit tests with mocked `Runner.run_streamed()` that yield controlled stream events
- Test each SSE event type (token, done, result, status, error) is properly formatted
- Test output validation: correct schema, wrong schema, missing output
- Test recording: verify `record_completed` called with correct params, verify `record_failed` on error
- Test pre-built agent path vs prompt-based agent path
- Fixtures: mocked `AiRunTimingHooks`, mocked `Runner`, pre-built `Agent`

**Priority: HIGH** — This is the backbone for all streaming endpoints. It's the only async streaming integration point with the Agents SDK. A bug here breaks real-time admin UI updates across all pipeline stages.

---

### 4. `llm/agents_sdk_service.py` — 44% (41/73 missing)

**What it does:** Agents SDK-backed LLM service (`AgentsSDKLLMService`). Wraps `Agent` + `Runner.run_sync()` behind the `LLMService` ABC. Handles guardrail registration, output guardrails, session persistence, and recording to `AiRunRepository` via `AiRunTimingHooks`.

**Uncovered paths:**
- `generate_with_usage()` execution path: `PROMPT_REGISTRY` lookup, `Agent()` creation with MCP servers and guardrails, `Runner.run_sync()` call with `RunConfig` + `max_tokens` (lines 138-252)
- `add_guardrail()` deprecated path with non-`OutputGuardrail` types
- Session save: `self._session_store.save()` with error swallowing on failure
- Recording on success: `self._recorder.record_completed()` with usage extraction
- Recording on failure: `self._recorder.record_failed()` after caught Exception
- `max_tokens` kwarg for `draft_writer` / `draft_section_writer` prompt names

**Tests needed:**
- Unit tests with mocked `Runner.run_sync()` — verify agent construction, guardrail passing, MCP server attachment
- Session save/replay: verify `session_store.save()` is called with correct state
- Recording both success and failure paths
- Test max_tokens kwarg is applied for draft prompts
- Test MCP server list is passed to Agent
- Fixtures: mocked `Runner`, mocked `AiRunRepository`, mocked `AgentSessionStore`

**Priority: HIGH** — This is the primary LLM backend for the agents_sdk configuration. It handles guardrails, session persistence, and recording. Any regression breaks all LLM calls when `AI_LAB_LLM_BACKEND=agents_sdk`.

---

### 5. `blog_ideas.py` — 47% (314/589 missing)

**What it does:** Blog idea CRUD, pipeline workflow (approve, generate outline/draft/review/marketing, publish), `run-next` unified endpoint, streaming idea endpoint, batch operations, claims extraction, link suggestions, thumbnail generation. Includes both in-memory and Postgres repositories.

**Uncovered paths:**
- Route handlers: `generate_ideas`, `generate_outline`, `generate_draft`, `review_technical`, `generate_marketing`, `publish_to_blog`, `schedule_publish`, `generate_thumbnail`, `batch_approve`, `run_next`, `extract_claims`, `suggest_links`, `list_ai_runs`, `list_claims`, `update_claim`, `get_generation_job` (most lines 328-1208)
- `_dispatch_or_run_generation()` branching logic: Postgres dispatches Celery, in-memory runs inline
- `_dispatch_generation_task()` helper
- `_run_next_extract_claims()` — claims extraction inline with LLM fallback
- `run_next()` pipeline decision tree: all 9+ state transitions (lines 343-1126)
- `generate_idea_stream()`: streaming endpoint with result-buffering and save logic
- `generate_outline` guard: validates idea.status == "approved"
- `generate_draft` guard: validates idea.outline_status == "approved"
- `review_technical` guard: validates idea.draft_status == "approved"
- `PostgresBlogIdeaRepository` methods: all CRUD operations with JSON serialization
- `_row_to_idea()` helper with JSON parsing and error handling
- `marketing_metadata_for_storage()` — normalization function

**Tests needed:**
- Integration tests via `TestClient` for each route handler
- Test `_dispatch_or_run_generation` both branches (inline for in-memory, Celery for Postgres)
- Full `run_next()` state machine: test each pipeline gate transition
- Idea streaming endpoint: mock `stream_generate`, verify SSE event flow and save
- Claims extraction endpoint: both LLM path and heuristic fallback path
- Thumbnail generation endpoint: success and failure (DALL-E returns None)
- Batch approve single/multiple/missing IDs
- Schedule publish: set and clear dates
- Postgres repository: CRUD with JSON round-trip (idea, outline, draft, review, marketing)
- Fixtures: `BlogIdeaRepository` seeded at every pipeline stage, `BlogRepository`, `ClaimsRepository`, `GenerationJobRepository`

**Priority: HIGH** — This is the core workflow module with the most business logic. The `run_next()` endpoint alone has a complex 9-branch decision tree. Postgres repository JSON serialization is entirely untested.

---

### 6. `blog_social.py` — 51% (197/401 missing)

**What it does:** Blog social features: reactions, bookmarks, comments (CRUD, moderation, nested threads), admin post moderation, feeds. Public and admin endpoints.

**Uncovered paths:**
- Comment moderation endpoints: approve/reject, admin bulk operations
- Nested comment thread resolution
- Feed/list endpoints with pagination
- Reaction validation (allowed emojis)
- Bookmark CRUD
- User identity header validation for social endpoints
- Error states: duplicate reaction, comment not found, bookmark already exists

**Priority: MEDIUM** — User-facing features but less critical than the core pipeline. Missing coverage on comment moderation and feed endpoints could allow untested admin actions. Reactions and bookmarks are simpler CRUD and lower risk.

---

### 7. `seo_analytics.py` — 47% (61/116 missing)

**What it does:** SEO analytics dashboard API. Computes aggregate stats, per-post SEO analysis (title length, meta description, keyword coverage), tag/keyword frequency.

**Uncovered paths:**
- `_analyze_seo()` scoring logic: title length checks, meta description checks, keyword presence
- Stats aggregation: computing averages, trends over time
- Post listing with SEO analysis per post
- Keyword frequency from blog tags

**Priority: MEDIUM** — Dashboard-only, not user-facing. Lower risk; data is read-only.

---

### 8. `ai_runs.py` — 46% (75/138 missing)

**What it does:** AI run tracking. Records LLM calls (completed/failed) with metadata (prompt, model, tokens, latency). Provides `list_latest`, `get_stats`, `list_for_entity`. In-memory and Postgres implementations.

**Uncovered paths:**
- `PostgresAiRunRepository`: all `record_completed`, `record_failed`, `list_latest`, `get_stats`, `list_for_entity` (lines 129-358)
- `_row_to_run()`: JSON deserialization with error handling
- `get_stats()` aggregation: per-stage stats, averages, success rate
- `list_for_entity()` filtering
- Error handling: `error_message[:2000]` truncation

**Tests needed:**
- Postgres repository CRUD via integration tests or mocked engine
- Stats computation with multiple runs, mixed completed/failed
- Entity filtering in `list_latest` and `get_stats`
- Edge cases: zero runs, zero completed, zero latencies
- Fixtures: `PostgresAiRunRepository` with `Engine` fixture

**Priority: MEDIUM** — Observability data; not in the critical path for any user operation. Low risk if broken.

---

### 9. `task_support.py` — 45% (67/122 missing)

**What it does:** Shared helpers for Celery tasks: repository factories, LLM service construction (backend selection, guardrail registration), MCP server building, job lifecycle tracking.

**Uncovered paths:**
- `_build_mcp_servers()`: MCP server construction when enabled
- `_build_llm_service()`: agents_sdk vs openai branch with session store + recorder
- `_register_blog_guardrails()`: guardrail registration for `AgentsSDKLLMService`
- `llm_service_for_news_item()`: news LLM service construction with RecordingLLMService fallback (lines 244-276)
- `track_job_lifecycle()`: mark job as running

**Priority: HIGH** (when combined with tasks.py and agents_sdk_service.py) — Orchestration layer connecting factories to services. Bug here misconfigures the entire LLM service stack.

---

### 10. `llm/service.py` — 55% (21/47 missing)

**What it does:** Abstract `LLMService` base class, `OpenAILLMService` (OpenAI SDK direct), `FakeLLMService` (test fake). `LLMGenerationError` exception.

**Uncovered paths:**
- `OpenAILLMService.generate_with_usage()`: `max_completion_tokens` for draft prompts, error handling from OpenAI API (lines 98-142)
- `generate()` wrapper method (delegates to `generate_with_usage`)
- `LLMGenerationError` raise paths

**Tests needed:**
- OpenAILLMService with mocked `self._client.beta.chat.completions.parse` — verify message construction, max_tokens passthrough, usage extraction
- Test `generate()` calls through to `generate_with_usage()`
- Fixtures: mocked OpenAI client

**Priority: HIGH** — The OpenAI direct backend path is used when `AI_LAB_LLM_BACKEND=openai`. Although the test infra exists for `FakeLLMService`, the real `OpenAILLMService` error handling and completion kwarg logic has zero coverage.

---

### 11. `llm/guardrails.py` — 41% (10/17 missing)

**What it does:** Post-generation guardrails using Agents SDK `@output_guardrail` decorators. Currently provides `claim_extraction_guardrail` that extracts claims from drafts using heuristic matching after `technical_review` output.

**Uncovered paths:**
- `_guardrail()` inner function: full logic (lines 45-64)
- Missing idea_id handling (returns early)
- Missing idea/idea.draft handling (returns early)
- `heuristic_claims_from_draft()` call and storage via `claims_repository.replace_for_idea()`
- `tripwire_triggered=False` always — guardrail is informational

**Tests needed:**
- Integration test: create guardrail with populated `BlogIdeaRepository`, mock a draft, verify claims are extracted and stored after guardrail runs
- Edge cases: empty idea_id, missing draft, None idea
- Verify guardrail is correctly registered on `AgentsSDKLLMService`
- Fixtures: `BlogClaimsRepository`, `BlogIdeaRepository` with seeded idea and draft

**Priority: MEDIUM** — Guardrails are informational (tripwire always False), but they extract claims that feed into the publishing gate. Broken guardrail means no claims are extracted automatically.

---

### 12. `generation_jobs.py` — 58% (40/96 missing)

**What it does:** Durable Celery job tracking for blog pipeline stages. Tracks queued -> running -> completed/failed lifecycle. In-memory and Postgres implementations.

**Uncovered paths:**
- `PostgresGenerationJobRepository`: `create_queued`, `get_by_celery_task_id`, `mark_running`, `mark_completed`, `mark_failed` (lines 86-189)
- `_update_status()` helper
- Error handling: rowcount check returns None

**Tests needed:**
- Postgres CRUD via integration tests or mocked engine (similar to ai_runs pattern)
- Lifecycle: queued -> running -> completed, queued -> running -> failed
- `mark_step` with non-existent task_id returns None

**Priority: MEDIUM** — Important for job tracking but not in the critical execution path. Postgres implementation is untested but follows same pattern as ai_runs.

---

### 13. `blog_claims.py` — 60% (47/117 missing)

**What it does:** Claim extraction and evidence ledger for blog ideas. LLM-based extraction with heuristic fallback. Postgres repository, status management.

**Uncovered paths:**
- `PostgresBlogClaimsRepository`: `replace_for_idea`, `get_by_id`, `update` (lines 73-133)
- `extract_claims_with_llm()`: LLM call with `ClaimExtractionResult` schema (lines 165-172)
- `validate_claims_ready_for_publish()`: blocking claim check (lines 191-208)
- `_initial_status()`: logic for pending vs supported based on claim_type

**Tests needed:**
- LLM extraction path with mocked service
- Heuristic fallback test (matches `_QUANTIFIED_RE`)
- Postgres repository CRUD with auto-status-update logic
- `validate_claims_ready_for_publish()` with blocking and non-blocking claims
- Fixtures: `BlogClaimsRepository`, `FakeLLMService` with `ClaimExtractionResult`

**Priority: MEDIUM** — Claims are the final gate before publishing. Broken extraction or validation could block or allow incorrect publication.

---

### 14. `news_extraction.py`, `news_sources.py` — both 67%

**What it does:** Article extraction from raw news items, news source management (CRUD, auth, validation).

**Uncovered paths:**
- Firecrawl extraction provider error handling
- Extraction retry/timeout logic
- Source CRUD: create, update, delete with validation
- Source auth token verification
- Dedup/content hash collision handling

**Priority: LOW** — Higher coverage than most modules and relatively stable news pipeline. Test gap is in firecrawl error handling and source auth.

---

## Summary of Required Test Infrastructure

### Common fixtures needed

| Fixture | Used by |
|---------|---------|
| `BlogIdeaRepository` seeded at various stages | blog_ideas, streaming_routes, tasks, blog_social, blog_claims |
| `FakeLLMService` with canned responses | tasks, blog_ideas, agents_sdk_service, service |
| `AiRunRepository` | ai_runs, streaming, agents_sdk_service, tasks |
| `GenerationJobRepository` | tasks, generation_jobs, blog_ideas |
| `BlogRepository` with published posts | blog_ideas, blog_social, blog_claims |
| `BlogClaimsRepository` with seeded claims | blog_claims, blog_ideas |
| Mocked `Runner.run_sync()` | agents_sdk_service |
| Mocked `Runner.run_streamed()` | streaming |
| Mocked OpenAI `beta.chat.completions.parse` | service (OpenAILLMService) |

### Test pattern references

The existing tests in `test_blog_agents_sdk.py` and `test_llm.py` show the established patterns:

1. **Repository isolation** — Use in-memory repositories with pre-seeded data
2. **Fake LLM** — `FakeLLMService` returns canned `BaseModel` instances, never calls real API
3. **TestClient integration** — `create_app()` with test Settings, verify routes via HTTP calls
4. **Celery eager mode** — `task_always_eager=True` for synchronous task execution in tests
5. **Auth headers** — Sign admin identity with `sign_admin_identity()` using test secret

---

## Quick-Win Recommendations

| Module | Quick fix | Effort |
|--------|-----------|--------|
| `llm/streaming.py` | Add unit tests with mocked `Runner.run_streamed` — covers SSE format, recording, error handling | 2 days |
| `streaming_routes.py` | Add integration tests mocking `stream_generate` — 4 endpoint handlers with status gates + save flow | 3 days |
| `tasks.py` | Add Celery eager-mode tests for blog pipeline tasks with `FakeLLMService` | 2 days |
| `llm/service.py` | Add OpenAI SDK mock tests for `OpenAILLMService` max_tokens + error handling | 1 day |
| `llm/agents_sdk_service.py` | Add unit tests with mocked `Runner.run_sync` — guardrails, sessions, recording | 2 days |
| `blog_ideas.py` | Add `TestClient` route tests + PostgreSQL repository round-trip tests | 3 days |
| `blog_social.py` | Add comment moderation + reaction CRUD tests | 2 days |
| `ai_runs.py` | Add PostgreSQL repository tests (same pattern as in-memory) | 1 day |

**Total estimated effort: ~16 days** to bring all modules above 70%.

---

## Risk Register

| Risk | Impact | Mitigation |
|------|--------|------------|
| Streaming endpoint error not sent to UI | User sees stalled loading state with no feedback | Test SSE error events in streaming_routes + llm/streaming |
| Draft retry loop exhausts without proper error | Empty draft stored silently | Test _generate_blog_draft retry paths in tasks.py |
| Pipeline state machine skips a gate | Publish occurs without technical review | Test all run_next() state transitions in blog_ideas.py |
| Postgres JSON serialization mismatch | Idea data silently corrupted in DB | Add Postgres repository round-trip tests |
| Guardrail claim extraction fails silently | Claims gate always empty, pipeline blocks | Test guardrail integration paths |
