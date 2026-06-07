# Streaming SSE — Real-Time AI Generation

The AI Lab Portal supports **Server-Sent Events (SSE)** streaming for real-time
generation of blog ideas, outlines, drafts, technical reviews, and marketing
metadata. This replaces the legacy Celery polling pattern with live token output.

## Architecture

```
Browser (StreamingIdeaGenerator)
  │ POST /api/admin/blog-ideas/generate-stream
  ▼
Next.js API Route (proxies with admin auth)
  │ POST /admin/blog-ideas/generate-stream/idea
  ▼
FastAPI endpoint
  │ stream_generate(prompt, schema, mcp_servers, hooks)
  ▼
Agents SDK Runner.run_streamed()
  │ SSE events: token | status | result | saved
  ▼
Browser receives tokens in real-time → redirects to detail page on completion
```

## Endpoints

### Blog Pipeline

| Stage | Endpoint | Validation |
|---|---|---|
| Idea | `POST /admin/blog-ideas/generate-stream/idea` | — |
| Outline | `POST /admin/blog-ideas/{id}/generate-stream/outline` | idea status = approved |
| Draft | `POST /admin/blog-ideas/{id}/generate-stream/draft` | outline status = approved |
| Review | `POST /admin/blog-ideas/{id}/generate-stream/review` | draft status = approved |
| Marketing | `POST /admin/blog-ideas/{id}/generate-stream/marketing` | draft status = approved |

### News Pipeline

| Stage | Endpoint | Validation |
|---|---|---|
| Scoring | `POST /admin/news/scoring/stream?article_id={id}` | article exists |

## SSE Event Format

Each event line is `data: {json}\n\n` where `{json}` has a `type` field:

```json
{"type": "token", "data": "text delta"}
{"type": "status", "status": "starting", "data": "Starting agent..."}
{"type": "result", "data": {"title": "...", ...}}
{"type": "saved", "idea_id": "idea_abc", "redirect_url": "/admin/blog-ideas/idea_abc"}
{"type": "error", "data": "error message"}
```

## Client-Side Consumption

Use the built-in `StreamingIdeaGenerator` React component:

```tsx
import { StreamingIdeaGenerator } from "@/components/admin/streaming-idea-generator";

<StreamingIdeaGenerator
  payload={{
    project_name: "My Project",
    project_summary: "...",
    ai_capabilities: "...",
    technical_highlights: "...",
    business_value: "...",
  }}
  sourceLabel="project"
/>
```

For custom consumption, POST to the Next.js API proxy:

```typescript
const response = await fetch("/api/admin/blog-ideas/generate-stream", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify(payload),
});
const reader = response.body!.getReader();
// Parse SSE events from ReadableStream
```

## MCP Tools

When `AI_LAB_LLM_MCP_ENABLED=true`, the agent has access to:

| Tool | Description | DB-backed |
|---|---|---|
| `blog_agent__idea_context` | Get project context for generation | ❌ |
| `blog_agent__idea_status` | Check pipeline status of an idea | ✅ blog_ideas |
| `blog_agent__search_posts` | Search published posts to avoid duplication | ✅ blog_posts |
| `news__source_reliability` | Get source credibility score | ✅ news_sources |
| `news__trending_topics` | Hot topics from recent published posts | ✅ blog_posts |
| `news__article_context` | Context about an extracted article | ✅ extracted_articles |

## Multi-Agent Patterns

### Blog: Technical Review + Claim Extraction

The technical review streaming endpoint uses a multi-agent pattern:
- **TechnicalReviewer** Agent (main)
- **ClaimExtractor** Agent (as a tool via `Agent.as_tool()`)

During review, the TechnicalReviewer can call `extract_claims` to extract
factual claims from the draft for evidence checking.

### News: Quality Review + Bias Detection

The news quality review uses a similar pattern:
- **NewsQualityReviewer** Agent (main)
- **NewsClaimExtractor** Agent (as a tool via `Agent.as_tool()`)

During review, the NewsQualityReviewer can call `extract_claims` to detect
bias, factual claims, and quality concerns in news articles.

## Configuration

| Env var | Values | Description |
|---|---|---|
| `AI_LAB_LLM_BACKEND` | `openai` (default) / `agents_sdk` | LLM backend |
| `AI_LAB_LLM_MCP_ENABLED` | `true` / `false` (default) | Enable MCP server tools |
| `AI_LAB_LLM_E2E_FAKE` | `true` / `false` (default) | Use fake LLM responses (testing) |

## Limitations

- Streaming requires `AI_LAB_LLM_BACKEND=agents_sdk`
- MCP tools require both `agents_sdk` backend AND `AI_LAB_LLM_MCP_ENABLED=true`
- The legacy Celery-based endpoints remain available for background generation
- MCP tools work with in-memory fallback when Postgres is unavailable
- News streaming scoring is currently in-memory only (Postgres support TBD)
