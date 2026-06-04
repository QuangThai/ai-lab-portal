# E05 X/Twitter Intelligence Planning Stub

## Status

blocked — entry criteria only

## Objective

Evaluate whether X/Twitter intelligence should become the next AI News source class, and define the minimum governance, provider, data, cost, and validation requirements before implementation starts.

This is a planning stub only. It does not authorize crawler, API, schema, queue, or UI implementation.

## Context

MVP 3 and post-MVP enhancements have already shipped lower-risk AI News capabilities:

- Official-source ingestion, extraction, exact deduplication, scoring, review, and public publish flow.
- Public topic filtering on `/ai-news`.
- Dedicated admin AI News review UI.
- Structured LLM scoring with heuristic fallback.
- User-submitted links feeding the same review pipeline.

X/Twitter remains higher risk because provider access, terms, rate limits, paid API cost, field semantics, and operational ownership are not yet accepted.

## Entry Criteria

Implementation can start only after all criteria are true:

1. **Provider strategy chosen**
   - Decide between official X API, a compliant third-party provider, manual/import workflow, or deferral.
   - Document terms-of-service constraints and allowed storage/redisplay behavior.

2. **Source scope defined**
   - Initial account list, keyword list, language scope, and inclusion/exclusion rules are approved.
   - Risk owner accepts that social data has higher spam, impersonation, and context-collapse risk than official RSS/blog sources.

3. **Data contract documented**
   - Required fields, nullable fields, timestamp semantics, engagement metrics, author metadata, URL references, and raw payload retention are documented.
   - Behavior is defined for deleted/private/unavailable posts.

4. **Budget and rate limits accepted**
   - API cost ceiling, rate-limit behavior, crawl frequency, backoff, and quota-exhaustion fallback are agreed.
   - No synchronous public/admin request may call the provider.

5. **Moderation and publish policy accepted**
   - X/Twitter items enter review as candidates only; no auto-publish.
   - Human review remains required before public display.
   - Attribution and source-link rules are defined.

6. **Validation plan exists**
   - Fake provider fixtures cover ingestion and scoring without real API calls.
   - Integration tests cover quota exhaustion, malformed payloads, duplicate links, and unavailable posts.
   - Story verify command is defined before implementation.

## Non-goals

- Do not implement provider calls in this stub.
- Do not add database migrations in this stub.
- Do not add X/Twitter UI surfaces in this stub.
- Do not scrape X/Twitter without an accepted provider/terms decision.
- Do not auto-publish social items.
- Do not build semantic/event deduplication as part of the first X/Twitter slice unless explicitly re-scoped.

## Candidate Stories

These are candidates, not approved implementation stories:

1. **US-051 Provider strategy decision record**
   - Create a durable decision documenting provider choice, terms constraints, cost ceiling, and ownership.

2. **US-052 X/Twitter source contract and fixtures**
   - Define source config shape, normalized raw item contract, and fake provider fixtures.

3. **US-053 X/Twitter ingestion spike behind fake provider**
   - Add ingestion path using fake provider only, with no real provider calls.

4. **US-054 Social item scoring calibration**
   - Tune scoring dimensions for social signals with nullable engagement metrics and spam/impersonation risk.

5. **US-055 Admin review affordances for social context**
   - Show author, source post URL, engagement metadata, and risk badges in the existing admin review UI.

## Blockers / Open Questions

- Which provider is acceptable under budget and terms?
- Are we allowed to store raw post payloads, author metadata, and engagement metrics?
- Are we allowed to display excerpts, summaries, or only source links?
- What is the first approved account/keyword list?
- Who owns false-positive, misinformation, impersonation, and takedown review?
- What monthly spend ceiling and quota-exhaustion behavior are acceptable?
- Should MVP 5 happen before GitHub/website crawler sources, which are lower risk and already listed as registry stubs?

## Exit Criteria for This Stub

This stub is complete when it is referenced from the roadmap and the Harness trace records that no MVP 5 implementation was started.
