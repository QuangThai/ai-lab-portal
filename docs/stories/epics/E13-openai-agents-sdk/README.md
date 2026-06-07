# E13 OpenAI Agents SDK Integration

Migrate the AI Blog Agent pipeline from direct OpenAI SDK calls to the OpenAI
Agents SDK (`openai-agents`) for structured multi-agent orchestration, native
guardrails, built-in tracing, and streaming real-time generation.

## Motivation

The original pipeline used Celery tasks making ad hoc `beta.chat.completions.parse()`
calls. This had growing pains:

| Issue | Resolution |
| --- | --- |
| Orchestration | `pipeline-next-stage.ts` on frontend → unified `/run-next` endpoint |
| Observability | Agents SDK hooks + custom `AiRunSpanProcessor` → PostgreSQL `ai_runs` table |
| Guardrails | `@output_guardrail` decorator → native Agents SDK `output_guardrails` |
| Human-in-the-loop | `AgentSessionStore` persists `RunState` for session-based approval |
| Provider flexibility | `LLMService` ABC with `OpenAILLMService` and `AgentsSDKLLMService` backends |
| Streaming | `Runner.run_streamed()` via SSE for real-time generation on all 5 stages |

## Architecture (After)

```text
Frontend: StreamingIdeaGenerator (SSE consumer)
  -> POST /api/admin/blog-ideas/generate-stream (Next.js proxy)
    -> POST /admin/blog-ideas/.../generate-stream/{stage} (FastAPI)
      -> stream_generate(prompt, schema, mcp_servers, hooks)
        -> Agent(output_guardrails, mcp_servers, tools)
        -> Runner.run_streamed()
        -> SSE events: token | status | result | saved
      -> Saves to repository
    -> Frontend redirects to detail page

Celery path (legacy):
  -> POST /admin/blog-ideas/.../generate-{stage} (FastAPI)
    -> Celery task
      -> LLMService.generate(prompt, inputs, schema)
      -> Agent(Runner.run_sync)
    -> Frontend polls GenerationJob
```

Both paths coexist. Toggle via `AI_LAB_LLM_BACKEND` (openai | agents_sdk).

## What Was Built

### Phase 1: Agents SDK Backend Option ✅
- `AgentsSDKLLMService` — wraps each pipeline stage as an `Agent` with
  instructions from `PROMPT_REGISTRY` and `output_type` from Pydantic schemas
- `Runner.run_sync()` for Celery workers (sync API)
- Backward compatible: same output shape as `OpenAILLMService`
- Switch via `AI_LAB_LLM_BACKEND=agents_sdk`

### Phase 2: Native Output Guardrails ✅
- `@output_guardrail` decorator in `guardrails.py`
- Passed directly to `Agent(output_guardrails=[...])`
- Replaced manual `add_guardrail()` + `_run_guardrails()` pattern
- `idea_id` captured from service instead of `inputs`

### Phase 3: Native Lifecycle Hooks ✅
- `AiRunTimingHooks(RunHooks)` — per-agent and per-LLM-call timing
- MCP tool call tracking via `on_tool_start/on_tool_end`
- Replaced `RecordingLLMService` wrapper for Agents SDK backend
- Foundation for future streaming and handoff tracking

### Phase 4: Streaming SSE (All 5 Stages) ✅
- `stream_generate()` — async generator yielding SSE events
- `Runner.run_streamed()` with `stream_events()` iteration
- Auto-saves result to repository after stream completes
- Endpoints:
  - `POST /admin/blog-ideas/generate-stream/idea`
  - `POST /admin/blog-ideas/{id}/generate-stream/outline`
  - `POST /admin/blog-ideas/{id}/generate-stream/draft`
  - `POST /admin/blog-ideas/{id}/generate-stream/review`
  - `POST /admin/blog-ideas/{id}/generate-stream/marketing`

### Phase 5: MCP Tools Integration ✅
- `backend/mcp_server/server.py` — FastMCP server with 3 tools
  - `blog_agent__idea_context` — project context
  - `blog_agent__idea_status` — pipeline status (DB-backed)
  - `blog_agent__search_posts` — content search (DB-backed)
- `MCPServerStdio` connected via `Agent(mcp_servers=[...])`
- Graceful in-memory fallback when DB unavailable
- Prompt registry updated with tool usage instructions

### Phase 6: Multi-Agent (Agent-as-tool) ✅
- `ClaimExtractor` Agent → `TechnicalReviewer` Agent via `Agent.as_tool()`
- Technical reviewer calls `extract_claims` during review
- `stream_generate()` accepts optional pre-built `Agent` parameter

### Phase 7: Observability Dashboard ✅
- `GET /admin/ai-observability/stats` — aggregated stats
- `GET /admin/ai-observability/runs` — recent run feed
- Frontend at `/admin/ai-observability` with stat cards, CSS bar charts, runs table
- Sidebar navigation link

### Phase 8: Streaming Frontend UI ✅
- `StreamingIdeaGenerator` client component — SSE consumer with token display
- `POST /api/admin/blog-ideas/generate-stream` Next.js API route proxy
- "Live stream" tab on `/admin/blog-ideas/new`
- Real-time token output with redirect on completion

## Key Files

| File | Purpose |
|---|---|
| `backend/app/llm/agents_sdk_service.py` | `AgentsSDKLLMService` wrapping Agent + Runner.run_sync |
| `backend/app/llm/hooks.py` | `AiRunTimingHooks` with timing + tool call tracking |
| `backend/app/llm/guardrails.py` | `@output_guardrail` native guardrails |
| `backend/app/llm/streaming.py` | `stream_generate()` async SSE generator |
| `backend/app/llm/review_agent.py` | Multi-agent: ClaimExtractor + TechnicalReviewer |
| `backend/app/llm/prompts.py` | Prompt registry with MCP tool instructions |
| `backend/app/streaming_routes.py` | All 5 streaming SSE endpoints |
| `backend/app/ai_observability_api.py` | Stats API for observability dashboard |
| `backend/mcp_server/server.py` | FastMCP server with DB-backed tools |
| `backend/app/task_support.py` | `_build_mcp_servers()` factory |
| `frontend/components/admin/streaming-idea-generator.tsx` | SSE consumer component |
| `frontend/app/admin/ai-observability/page.tsx` | Dashboard page |

## Architecture Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Backend default | `OpenAILLMService` | `AgentsSDKLLMService` is opt-in via env var |
| Streaming transport | SSE via `StreamingResponse` | Native HTTP streaming, works with Next.js proxy |
| MCP transport | `MCPServerStdio` | No network overhead, subprocess lifecycle managed by SDK |
| Tool call tracking | `AiRunTimingHooks` hooks | Native SDK lifecycle, no additional instrumentation |
| Claim extraction | Agent-as-tool via `as_tool()` | Proper multi-agent pattern vs handoffs for HITL |
| Charting | CSS bar charts (no external lib) | Zero dependencies, sufficient for simple metrics |

## Extension: News Pipeline

The Agents SDK architecture was extended to the **News Pipeline** in a
follow-up initiative, mirroring the same patterns:

| Blog Feature | News Equivalent |
|---|---|
| Blog streaming SSE | `POST /admin/news/scoring/stream` |
| MCP blog tools | `news__source_reliability`, `news__trending_topics`, `news__article_context` |
| Multi-agent (ClaimExtractor) | `NewsClaimExtractor` + `NewsQualityReviewer` |
| Observability dashboard | Entity type filter (`?entity_type=ai_news_scoring`) |
| StageStreamButton | `NewsStreamButton` component |
| SEO & Analytics | `/admin/seo-analytics` dashboard |

---

## Deferred

- **Agent handoffs**: The HITL pipeline (human approval between each stage)
  doesn't map cleanly to automatic handoffs. The current state machine approach
  (`pipeline-next-action.ts` + `/run-next`) is the correct design for HITL.
- **Removing Celery**: Still needed for background tasks (RSS crawling, etc.).
  Streaming is a parallel path, not a replacement.

## Exit Criteria

- [x] `AgentsSDKLLMService` produces identical structured outputs as `OpenAILLMService` for all prompt types
- [x] Full test suite passes (306 tests) with both backends
- [x] Agents SDK tracing visible in `ai_runs` table via `AiRunSpanProcessor`
- [ ] ~~Agent handoffs~~ — Deferred (HITL pipeline incompatible)
- [x] Claim extraction as native output guardrail
- [x] Streaming SSE for all 5 pipeline stages
- [x] MCP tools server with DB-backed tools
- [x] Observability dashboard
- [x] Multi-agent pattern via Agent-as-tool
