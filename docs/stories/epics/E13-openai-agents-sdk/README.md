# E13 OpenAI Agents SDK Integration

Migrate the AI Blog Agent pipeline from direct OpenAI SDK calls to the OpenAI
Agents SDK (`openai-agents`) for structured multi-agent orchestration, native
guardrails, built-in tracing, and human-in-the-loop support.

## Motivation

The current pipeline works, but each stage (idea, outline, draft, review,
marketing, claims) is a separate Celery task making ad hoc
`beta.chat.completions.parse()` calls. This design has growing pain:

| Issue | Current state |
| --- | --- |
| Orchestration | `pipeline-next-stage.ts` on the frontend decides *what runs next* — the backend has no awareness of the pipeline graph |
| Observability | LLM calls are recorded to `ai_runs` table, but there is no end-to-end trace linking prompt → agent → human gate → next agent |
| Guardrails | Claim extraction is a separate LLM call with manual handling; no native pre/post-condition hooks |
| Human-in-the-loop | Approval gates are frontend-only PATCH actions; agents don't *know* they're waiting for human input |
| Provider flexibility | Hard-coded to OpenAI `beta.chat.completions.parse()` via `OpenAILLMService` |
| Testability | Fake responses work but require maintaining a parallel `FakeLLMService` with canned Pydantic instances |

## Current Architecture (Before)

```text
Frontend: pipeline-next-stage.ts (decides next step)
  -> Server action: approveAndRunNext()
    -> PATCH /api/blog-ideas/{id} (approve gate)
    -> POST /api/blog-ideas/{id}/generate-{stage} (Celery task)
      -> LLMService.generate("prompt_name", inputs, output_schema)
        -> OpenAI beta.chat.completions.parse()
      -> AiRunRepository.record() (manual audit log)
    -> Frontend polls GenerationJob status
```

## Target Architecture (After)

```text
Frontend: approve gate -> unified "run next" endpoint
  -> Backend: Runner.run() with Agents SDK
    -> Agent (with handoff to next agent)
    -> Built-in tracing (span per agent run)
    -> Output guardrails for claim validation
    -> Human-in-the-loop for approval gates (async handoff)
    -> AiRunRepository.record() via lifecycle hooks
```

## Integration Approach

### Phase 1: Additive — Agents SDK as an LLM backend option

Replace `OpenAILLMService.generate_with_usage()` internals with Agents SDK's
`Runner.run()` while keeping the `LLMService` abstraction. This means:

- The `LLMService` ABC stays — existing Celery tasks and `FakeLLMService` continue
  unchanged.
- A new `AgentsSDKLLMService` wraps each pipeline stage as an `Agent` with
  instructions from `PROMPT_REGISTRY` and `output_type` from existing Pydantic
  schemas.
- Agents SDK tracing captures per-stage spans automatically.
- Switch is configurable via environment variable (`AI_LAB_LLM_BACKEND=agents_sdk`).
- `FakeLLMService` can be replaced by Agents SDK's built-in test hooks.

**Files to create/modify:**
- `backend/app/llm/agents_sdk_service.py` — new `AgentsSDKLLMService`
- `backend/app/llm/service.py` — add factory function for backend selection
- `backend/app/llm/e2e_fake_responses.py` — can simplify using Agents SDK test utils
- `backend/.env.example` — add `AI_LAB_LLM_BACKEND`

### Phase 2: Agent Handoffs for Pipeline Orchestration

Replace the frontend-driven `pipeline-next-stage.ts` orchestration with actual
agent-to-agent handoffs on the backend. Each pipeline stage becomes a dedicated
Agent that hands off to the next stage on approval.

```python
idea_agent = Agent(
    name="Idea Generator",
    instructions=PROMPT_REGISTRY["blog_idea"].system,
    output_type=BlogIdea,
    handoffs=[outline_agent],  # after human approval
)
```

The approval gate becomes a session-based pause: the agent waits for a human
signal (via a `needs_approval` tool or session checkpoint) and resumes the
handoff chain.

**Backend changes:**
- New unified `/api/blog-ideas/{id}/run-next` endpoint
- Deprecate individual `/generate-outline`, `/generate-draft`, etc.
- Pipeline graph lives in Python, not in `pipeline-next-stage.ts`

**Frontend changes:**
- Simplify `pipeline-next-stage.ts` to a single "run next" call
- Keep pipeline stepper UI for human visibility
- Human approval becomes an input to the agent session

### Phase 3: Guardrails for Claim Validation

Replace the separate `claim_extraction` LLM call with Agents SDK output
guardrails that run automatically after the draft review stage.

```python
@output_guardrail
async def claim_guardrail(
    context, agent, output: TechnicalReview
) -> GuardrailFunctionOutput:
    # Check each issue for unsupported claims
    ...
```

This eliminates the dedicated claims CLI/extraction endpoint and makes claim
checking automatic on every technical review.

### Phase 4 (Future): Realtime Agents

Explore `gpt-realtime-2` and voice agents for author-facing productivity tools
(e.g., "read my draft aloud and suggest edits").

## Story Candidates

| Story | Title | Phase | Description |
| --- | --- | --- | --- |
| US-091 | Agents SDK backend option | 1 | ✅ implemented |
| US-092 | Agents SDK E2E with fake provider | 1 | ✅ implemented — 10 integration tests proving factory, recording, and backend parity |
| US-093 | Pipeline handoff migration | 2 | ✅ implemented — unified `/run-next` endpoint with pipeline state machine in Python, 4 tests |
| US-094 | Human-in-the-loop via agent sessions | 2 | ✅ implemented — AgentSessionStore saves/loads RunState per idea_id; integrated with AgentsSDKLLMService; 4 session tests |
| US-095 | Claim guardrails | 3 | ✅ implemented — post-generation guardrail system, claim extraction via heuristic on technical_review, 3 tests |
| US-096 | Trace quality with Agents SDK spans | 1+ | ✅ implemented — AiRunSpanProcessor, trace_id column on ai_runs, migration 0034, 5 tracing tests |
| US-097 | Observability dashboard | 1+ | ✅ implemented — AI Runs table on blog idea detail page showing prompt/status/tokens/latency per generation |

## Architecture Decisions Needed

| Decision | Options | Recommended |
| --- | --- | --- |
| Session storage | In-memory vs Redis-backed | Redis (existing Redis infra + durable sessions across Celery restarts) |
| Backend default | Keep `OpenAILLMService` as default | Yes — `AgentsSDKLLMService` is opt-in via env var until Phase 2 |
| Frontend orchestration removal | Complete in Phase 2 vs incremental per-stage | Incremental per-stage — one story replaces one endpoint at a time |
| Tracing storage | Agents SDK file tracing vs custom exporter | Custom exporter to PostgreSQL `ai_runs` table (backward compat with existing audit) |
| Agent instructions source | Inline Python vs PROMPT_REGISTRY | Keep PROMPT_REGISTRY — instructions are versioned and testable |

## Validation Shape

| Layer | Expected proof |
| --- | --- |
| Unit | `AgentsSDKLLMService.generate_with_usage()` returns same Pydantic output as `OpenAILLMService` for each pipeline stage |
| Integration | Full pipeline (idea → publish) with fake agents produces same blog post shape |
| E2E | Playwright golden path: generate → approve → publish with Agents SDK backend |
| Platform | Docker Compose with `AI_LAB_LLM_BACKEND=agents_sdk` passes E2E suite |

## Non-goals

- Realtime / voice agents (Phase 4, deferred)
- Full auto-publish (human-in-the-loop stays)
- Author self-serve agent (separate epic)
- Removing Celery entirely (async job queue still needed for long-running agent runs)
- Migration of AI News pipeline (scope-limited to Blog Agent)

## Exit Criteria

- [ ] `AgentsSDKLLMService` produces identical structured outputs as `OpenAILLMService` for all 7 prompt types
- [ ] Full E2E golden path passes with both backends (env-var toggle)
- [ ] Agents SDK tracing visible in admin (span timeline per blog idea)
- [ ] At least one pipeline stage uses agent handoffs instead of frontend orchestration
- [ ] Claim validation is an output guardrail, not a separate endpoint
