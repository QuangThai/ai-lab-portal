# 0012 Content Agent Pipeline Architecture

Date: 2026-06-09

## Status

Accepted

## Context

The AI Lab Portal had a robust AI Blog Agent pipeline (idea -> outline -> draft -> review -> marketing -> SEO -> claims -> publish) backed by `LLMService` (supporting `OpenAILLMService` and `AgentsSDKLLMService`), a prompt registry, structured Pydantic outputs, and Celery job infrastructure. Three new agent capabilities were needed to extend the content lifecycle beyond the core pipeline:

1. **Content Repurposing** — Transform published blog posts into Twitter threads, LinkedIn articles, and summary snippets to maximize content reach.
2. **Auto-Scheduling** — Analyze content readiness, calendar context, and historical engagement data to suggest optimal publish times.
3. **SEO Auto-Optimize** — Close the loop between SEO audit results and content improvement by applying audit recommendations to draft content.

All three agents share common design constraints:
- They must operate after core pipeline stages complete (repurpose after publish, schedule after approval, SEO after audit).
- All outputs require explicit admin review before any action is taken (no auto-apply).
- They must work with both LLM backends (`OpenAILLMService` and `AgentsSDKLLMService`) via the existing `LLMService` ABC.
- Each needs a fake provider matching the project's `e2e_fake_responses.py` pattern for testability.
- No external API integrations for MVP (no Twitter/LinkedIn posting, no external SEO tools).

## Decision

Build the three agents as standalone modules following a consistent architecture pattern:

1. **Module structure per agent** — Each agent lives in its own module (`content_repurpose.py`, `scheduling_agent.py`, `seo_optimizer.py`) with:
   - Pydantic output models for structured, schema-validated results.
   - An abstract service interface (ABC) with `generate()` method.
   - A concrete `LLMBackendService` that calls `LLMService.generate_with_usage()`.
   - A `FakeService` that returns realistic mock data from `e2e_fake_responses.py`.
   - Service resolution via the existing `AI_LAB_LLM_BACKEND` env var pattern.

2. **Human-in-the-loop** — Agent outputs are always presented to an admin for review and explicit acceptance/rejection:
   - Repurposing: Admin views generated social content, copies to clipboard manually. No auto-posting.
   - Scheduling: Admin sees the suggested date/time with rationale, can accept, modify, or publish immediately.
   - SEO: Admin reviews a before/after diff per section and accepts/rejects each change individually.

3. **Backend integration** — Each agent exposes a REST API endpoint under `/admin/`:
   - `POST /admin/blog-posts/{id}/repurpose`
   - `POST /admin/scheduling/suggest/{post_id}`
   - `POST /admin/seo/optimize/{idea_id}`
   - Results are stored in database tables (`repurposed_content`, scheduling metadata on blog_ideas, SEO changes) for audit and review.

4. **Frontend integration** — Admin UI buttons and review panels:
   - Repurpose: Button on published blog post detail page, review panel with copy buttons.
   - Schedule: Suggestion display in the publish step UI, content calendar integration.
   - SEO: "Auto-optimize SEO" button after SEO audit, diff review panel with per-section accept/reject.

5. **Output storage** — Each agent's generated content is persisted:
   - Repurposed content stored as JSONB per platform in `repurposed_content` table.
   - Scheduling suggestion stored on `blog_ideas.scheduled_at` after admin confirmation, with Celery periodic task for auto-publish.
   - SEO changes stored for audit with acceptance status per change section.

## Alternatives Considered

1. **Single monolithic "Agent Service"** — Rejected because each agent has different output formats, storage requirements, and review UIs. Separate modules keep each one testable and independently maintainable.
2. **Auto-publish/auto-apply without review** — Rejected because it contradicts the product principle that all AI-generated content requires human approval before affecting the public surface.
3. **Extend the core pipeline with more steps** — Rejected because repurposing and scheduling operate after the pipeline completes (publish is the terminal step), and SEO optimization is a post-audit refinement, not a pipeline stage.

## Consequences

Positive:

- Each agent is independently testable, deployable, and maintainable.
- The LLM-agnostic pattern means agents work with both OpenAI and Agents SDK backends without code changes.
- Admin review gates prevent unvalidated AI content from reaching the public surface.
- Fake providers enable reliable E2E testing without real LLM calls.

Tradeoffs:

- Three new modules mean more code surface to maintain.
- No external API integration limits automation (manual copy-paste for social media).
- The agents add UI complexity to the admin panel (additional buttons, review panels, diff viewers).

## Follow-Up

- Consider integrating OpenAI Agents SDK for more sophisticated multi-step orchestration (e.g., repurpose + schedule in one agent session).
- Add external API posting for social media when platform API keys are available and terms are accepted.
- Extend SEO optimization with image alt-text and schema.org markup generation.
