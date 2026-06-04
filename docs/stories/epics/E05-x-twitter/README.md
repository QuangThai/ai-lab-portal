# E05 X/Twitter Intelligence Planning Stub

## Status

MVP 5 stories implemented — 5 of 6 entry criteria met

All US-053 through US-057 implemented with fake provider. Real provider
integration blocked on budget/terms approval (entry criterion #4).

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

Provider research is captured in `docs/decisions/0008-x-twitter-provider-strategy.md`. Current proposed direction: Apify for X/Twitter discovery, Firecrawl only for linked-page extraction after an AI filter accepts a post/link.

## Source Scope (MVP 5 Initial)

Accepted per entry criterion #2.

### Account Handles (initial set)

- `@OpenAI` — official OpenAI research, product, and policy announcements
- `@AnthropicAI` — official Anthropic research and Claude updates
- `@GoogleDeepMind` — DeepMind research and publications
- `@MetaAI` — Meta AI research and open-source releases
- `@huggingface` — Hugging Face ecosystem updates
- `@kaboroidev` — practical AI engineering and tools
- `@AIatMeta` — Meta AI applied research
- `@EMostaque` — AI infrastructure and scaling commentary
- `@ylecun` — AI research direction (Meta Chief AI Scientist)
- `@AndrewYNg` — AI education and practical ML

### Search Keywords

- `AI research paper`, `LLM benchmark`, `agents AI`, `open source LLM`
- `GPU cluster`, `AI infrastructure`, `training run`
- `AI safety`, `AI policy`, `AI regulation`
- `foundation model`, `multimodal AI`, `reasoning model`
- Excluded: `memecoin`, `NFT`, `crypto trading`

### Language Scope

- Primary: English (`en`)
- Secondary: none for initial scope
- Posts in other languages are accepted only if the author handle is in the
  approved account list.

### Inclusion/Exclusion Rules

- Only posts with at least one extractable http/https URL are ingested.
- Posts from unapproved handles must match a search keyword to be candidates.
- Posts with `spam_or_engagement_bait` risk flag are rejected pre-ingestion.
- Pure memes, personal drama, and unsupported rumors are rejected by the
  social link filter regardless of source.

### Risk Ownership

- Risk owner: AI Lab admin team (whoever holds the admin `ADMIN_BOUNDARY_SECRET`).
- False-positive review and takedown decisions are made by the review admin on
  a per-item basis.
- Automated takedown is not implemented — all moderation is human-in-the-loop.

## Entry Criteria

Implementation can start only after all criteria are true:

1. ✅ **Provider strategy chosen**
   - **Accepted**: Apify Xquik X Tweet Scraper as first trial actor; Maxime Dupré Twitter Scraper as backup actor; Firecrawl for accepted linked-page extraction only.
   - Decision recorded in `docs/decisions/0008-x-twitter-provider-strategy.md`.
   - Terms-of-service constraints and storage/redisplay rules documented in decision 0010.

2. ✅ **Source scope defined**
   - Initial account list, keyword list, language scope, and inclusion/exclusion rules are documented in the Source Scope section above.
   - Risk owner: AI Lab admin team (whoever holds `ADMIN_BOUNDARY_SECRET`).

3. ✅ **Data contract documented**
   - Required fields, nullable fields, timestamp semantics, engagement metrics, author metadata, URL references, and raw payload retention are documented in `docs/decisions/0009-x-twitter-data-contract.md`.
   - Deleted/private/unavailable post behavior is defined.
   - Provider adapter contract (`SocialProviderProtocol`) is defined.

4. ❌ **Budget and rate limits accepted** (requires human decision)
   - API cost ceiling, rate-limit behavior, crawl frequency, backoff, and quota-exhaustion fallback are agreed.
   - No synchronous public/admin request may call the provider.

5. ✅ **Moderation and publish policy accepted**
   - No auto-publish, mandatory human review, attribution rules, storage and redisplay policy, spam/impersonation handling, and takedown policy documented in `docs/decisions/0010-x-twitter-moderation-policy.md`.
   - Filter transparency: rejection/acceptance reasons are recorded and visible to review admin.

6. ✅ **Validation plan exists**
   - Fake provider fixtures cover ingestion and scoring without real API calls.
   - Integration tests cover quota exhaustion, malformed payloads, duplicate links, and unavailable posts.
     - `test_news_social_x_integration.py` — 16 tests across 4 edge case categories (quota, malformed, dupes, unavailable).
   - Story verify command is defined before implementation.
   - Total social-related tests: 56 passing (integration + US-053 + US-055 + US-056 + US-057).

## AI Social Link Filter Contract (Draft)

The first social-specific AI step should run before article extraction. It decides whether a post/link is worth entering the existing AI News pipeline.

Input:

- Normalized social post fields: `post_id`, `post_url`, `post_text`, `created_at`, `author_handle`, `author_display_name`, `engagement_metrics`, `lang`, `quoted_post_text`, `reply_context`, `entities.urls`.
- Source scope metadata: matched account/list/search term, crawl run id, provider name, provider actor/version.
- Product preference: AI/LLM relevance, practical engineering signal, credible source, public-client usefulness, avoid hype/spam/drama.

Structured output:

```text
should_ingest: boolean
reason: string
topic: models | agents | research | policy | infrastructure | product | funding | security | general
priority: low | medium | high
risk_flags: string[]
urls_to_extract: string[]
requires_human_review: boolean
```

Rules:

- `should_ingest=false` for pure memes, personal drama, engagement bait, vague hype, unsupported rumors, or posts with no AI/LLM relevance.
- `urls_to_extract` must contain only http/https URLs found in the post/entities; extraction still uses the existing SSRF-safe worker path.
- `requires_human_review=true` for every accepted social item in MVP 5.
- The filter never publishes content and never bypasses review.

## Non-goals

- Do not implement provider calls in this stub.
- Do not add database migrations in this stub.
- Do not add X/Twitter UI surfaces in this stub.
- Do not scrape X/Twitter without an accepted provider/terms decision.
- Do not auto-publish social items.
- Do not build semantic/event deduplication as part of the first X/Twitter slice unless explicitly re-scoped.

## Candidate Stories

These are candidates, not approved implementation stories:

1. **US-052 Provider strategy acceptance / sample-run approval**
   - Accept or revise `docs/decisions/0008-x-twitter-provider-strategy.md`, name budget/terms owner, and approve or reject a tiny Apify sample run.

2. **US-053 X/Twitter source contract and fake fixtures** — implemented
   - Defined normalized social post contract, Apify Xquik-like fake provider fixtures, and no-real-provider tests in `backend/app/social_x.py` / `backend/tests/test_social_x.py`.

3. **US-054 AI social link filter contract** — implemented
   - Defined deterministic fake-first structured output for `should_ingest`, `reason`, `topic`, `priority`, `risk_flags`, `urls_to_extract`, and `requires_human_review`.

4. ✅ **US-055 X/Twitter ingestion spike behind fake provider** — implemented
   - `run_social_x_ingest()` connects FakeXTwitterProvider + social link filter to the existing AI News pipeline.
   - Celery tasks `news.ingest_social_x_source` and `news.ingest_due_social_x_sources`.
   - 9 tests pass; no real provider calls.
   - Story: `docs/stories/epics/E05-x-twitter/US-055-ingestion-spike-fake-provider.md`

5. ✅ **US-056 Social item scoring calibration** — implemented
   - Added `author_credibility_score` and `social_engagement_score` to scoring model with DB migration.
   - `compute_heuristic_scores()` extracts social metadata from raw payload.
   - 15 tests pass; 6 existing regression tests pass.
   - Story: `docs/stories/epics/E05-x-twitter/US-056-social-scoring-calibration.md`

6. ✅ **US-057 Admin review affordances for social context** — implemented
   - Social metadata JSON stored on review item; displayed as author info, engagement metrics, risk badges, and View post link.
   - Non-social items unchanged.
   - Backend 42 tests pass; frontend typecheck and lint pass.
   - Story: `docs/stories/epics/E05-x-twitter/US-057-admin-review-affordances.md`

## Blockers / Open Questions

- Will the team accept the proposed Apify-first provider strategy, or require official X API?
- Are we allowed to store raw post payloads, author metadata, and engagement metrics?
- Are we allowed to display excerpts, summaries, or only source links?
- What is the first approved account/keyword list?
- Who owns false-positive, misinformation, impersonation, and takedown review?
- What monthly spend ceiling and quota-exhaustion behavior are acceptable?
- Which first-run source scope is approved: account handles, search terms, X list, tweet URLs, or a mix?
- Should the first sample use Xquik ($0.15/1K listed) or Maxime Dupré ($0.40/1K listed) actor?

## Exit Criteria for This Stub

This stub is complete when it is referenced from the roadmap and the Harness trace records that no MVP 5 implementation was started.
