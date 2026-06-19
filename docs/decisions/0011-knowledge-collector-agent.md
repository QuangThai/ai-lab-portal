# 0011 Knowledge Collector Agent Architecture

Date: 2026-06-09

## Status

Accepted

## Context

The AI Blog Agent pipeline originally had Knowledge Collection as a silent background service (`KnowledgeService`) that enriched LLM prompts with context from projects, blog posts, showcases, and news. It was wired into streaming routes and Celery tasks but had zero tests, no visible pipeline step in the admin UI, no persistent storage of collected context, and no way for admin operators to review or edit context before generation.

The pipeline step order at the time was:

```
idea -> outline -> draft -> review -> marketing -> seo -> claims -> publish
```

Knowledge context was fetched on every LLM call via live database queries, meaning:
- Operators could not audit what context the AI had used for a given idea.
- The same queries ran repeatedly for every pipeline stage.
- There was no human review gate before context was fed to generation.
- The service had no test coverage.

## Decision

Add a visible, agent-driven Knowledge Collection stage to the blog-ideas pipeline stepper between idea creation and outline generation:

1. **New pipeline step** — "Collect Context" is inserted between idea approval and outline generation. The step order becomes:
   ```
   idea -> collect -> outline -> draft -> review -> marketing -> seo -> claims -> publish
   ```
2. **Persistent storage** — A `knowledge_contexts` database table stores collected context per idea (project data, related posts, showcases, news) with audit columns (`raw_collected_at`, `approved_at`, `approved_by`, `edited_at`).
3. **Admin review UI** — Operators view collected context in a review card on the blog idea detail page with source attribution, editable fields, and an approve button.
4. **Approval gate** — The pipeline does not advance to outline generation until an admin explicitly approves the collected context.
5. **Tests** — Full test coverage for KnowledgeService, KnowledgeContextRepository, API endpoints, and pipeline stepper integration.
6. **Backend stack** — FastAPI endpoints (`POST /admin/knowledge/collect`, `GET /admin/knowledge/context/{idea_id}`, `PATCH /admin/knowledge/context/{idea_id}`, `PATCH /admin/knowledge/context/{idea_id}/approve`), Pydantic models, Alembic migration, and InMemory + Postgres repository implementations matching the project's existing patterns.

## Alternatives Considered

1. **Keep as silent background enrichment** — Rejected because operators have no visibility into what context the AI uses, increasing hallucination risk and reducing auditability.
2. **Agent-only collection with OpenAI Agents SDK** — Rejected for phase 1 because it would add orchestration complexity before the collection behavior was validated. Can be added in a follow-up phase.
3. **Auto-collect on idea creation** — Simpler UX but removes the human review opportunity, contradicting the product principle that all AI pipeline stages require human approval before advancing.

## Consequences

Positive:

- Operators can audit, edit, and approve context before it reaches LLM generation, reducing hallucination risk.
- The `knowledge_contexts` table provides a full audit trail for every idea.
- The existing `KnowledgeService` queries are now replaced by stored context, reducing live query load.
- Test coverage eliminates the previous zero-test gap on knowledge collection.

Tradeoffs:

- Adds one more manual step to the pipeline (collect + approve), increasing time from idea to outline.
- Existing ideas with no context row must be handled during migration.

## Follow-Up

- Add agent-based orchestration (OpenAI Agents SDK) for multi-source collection in a future phase.
- Consider auto-collect with human review as a faster path for low-risk ideas.
