# AI Lab Portal Product Overview

## Purpose

AI Lab Portal is the public and internal platform for repositioning the company
from an IT outsource/offshore development provider into an AI/LLM Lab. The
portal must demonstrate real AI product capability, publish credible AI Lab
content, and turn market intelligence into sales-ready proof.

## Product Goals

1. Build credibility with potential clients by showing practical AI products,
   AI engineering lessons, and evaluation practices.
2. Create a repeatable content and intelligence engine for sales, marketing,
   and leadership.
3. Make the system itself explainable as an AI workflow showcase.

## Primary Product Surfaces

Public website:

- `/`
- `/lab`
- `/showcases`
- `/showcases/[slug]`
- `/blog`
- `/blog/[slug]`
- `/ai-news`
- `/ai-news/[slug]`
- `/ai-news/submit`
- `/contact`

Internal admin dashboard:

- Blog ideas, drafts, reviews, and published posts.
- News raw items, review queue, published/rejected items, and duplicate groups.
- Sources, topics/tags, showcases, prompt/scoring settings, and jobs.

## MVP Modules

### AI Blog Agent

Turns approved company/project context into blog ideas, outlines, drafts,
technical reviews, marketing metadata, and publishable posts. Human approval is
required before publication in MVP.

### AI News Intelligence Feed

Ingests lower-risk AI sources first, stores raw input, extracts linked content,
deduplicates items, scores relevance/quality/spam risk, summarizes candidates,
and routes them to human review before publication.

## Locked MVP Rules

- Public content must be fast, SEO-friendly, and safe to cache.
- Admin operations require authentication and role-based authorization.
- Public publishing requires human approval.
- External provider payloads are untrusted and must be parsed before use.
- AI structured outputs must be schema-validated before application logic uses
  them.
- Crawling and AI jobs must be asynchronous and retryable.
- Raw external input must be retained before normalization for audit/debugging.
- Auto-approve is disabled in MVP.
- Auto-reject is allowed only for clearly low-quality or duplicate items until
  evaluation data supports stronger automation.

## Out of Scope for MVP

- Fully autonomous publishing.
- Large-scale whole-web crawling.
- Paid newsletter functionality.
- Advanced CRM integration.
- Fine-tuned custom models.
- Full enterprise user management.
- X/Twitter ingestion before provider strategy, cost/rate limits, and terms are
  explicitly settled.
