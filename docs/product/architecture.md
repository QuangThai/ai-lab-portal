# AI Lab Portal Architecture Contract

## Architecture Goals

The architecture must support three outcomes:

1. Public credibility: fast, clean, SEO-friendly public pages.
2. Internal AI workflow automation: asynchronous crawling, scoring, writing,
   review, deduplication, and publishing workflows.
3. Showcase value: an explainable architecture that can be reused as a client
   delivery reference.

## Accepted MVP Stack

Frontend:

- Next.js with TypeScript.
- Tailwind CSS.
- Better Auth for MVP admin authentication in the Next.js frontend.
- shadcn/ui or equivalent component primitives for admin UI.
- React Query may be added later for admin server state after API contracts exist.
- MDX or markdown rendering for blog content.
- SSR/SSG/caching for SEO-heavy public pages.

Backend:

- Python FastAPI.
- Pydantic for request/response and AI structured-output validation.
- SQLAlchemy 2.x or SQLModel.
- Alembic migrations.
- REST API with OpenAPI docs.

Data and async runtime:

- PostgreSQL as system of record.
- pgvector for MVP embedding similarity/deduplication.
- Redis for cache, rate limiting, and queue broker.
- Celery workers and scheduler for crawl/AI/dedup/publish jobs.
- S3-compatible object storage for large raw payloads, extracted markdown,
  images, and debug artifacts.

AI and provider boundary:

- LLM provider abstraction.
- Embedding provider abstraction.
- Prompt registry and prompt versions.
- Structured outputs validated by application schemas.
- Provider payloads stored raw or referenced before normalization.

## Layering Rules

Implementation should follow the repository architecture rule:

```text
domain <- application <- infrastructure <- interface <- app surfaces
```

- Domain/application code must not depend on framework, UI, provider clients,
  concrete database clients, or process environment.
- Interface layers parse unknown input into DTOs/commands before inner code sees
  it.
- Infrastructure owns concrete database, provider, queue, logging, and storage
  adapters.
- App surfaces call API contracts or app-facing clients, not domain internals.

## Boundary Inputs

The following inputs are untrusted and must be parsed/validated at boundaries:

- HTTP bodies, route params, query strings, and cookies.
- Session/JWT/identity claims.
- Environment variables.
- Database rows returned from concrete clients.
- Crawled pages, RSS entries, GitHub payloads, Firecrawl output, Apify dataset
  items, X/Twitter API payloads, and user-submitted URLs.
- AI model outputs.

## Cross-Cutting Requirements

- Public list APIs are paginated.
- API errors use a standard error envelope.
- Long-running operations return job ids and run asynchronously.
- Important mutations create audit logs.
- Application logs are operational records; audit logs are product records.
- Secrets never reach frontend code or logs.
- Provider errors are categorized as transient, rate-limited, authentication,
  validation, or permanent failures.

## Accepted Auth Boundary

- MVP admin authentication uses Better Auth in the Next.js frontend. See
  `docs/decisions/0007-admin-auth-strategy.md`.
- Better Auth owns login/session cookie handling under Next.js routes.
- FastAPI remains the domain API and must validate any authenticated identity
  passed from the frontend/server boundary before handling admin mutations.
- Authorization is not solved by login. Role checks and audit attribution must
  be designed before admin CRUD or publishing workflows.
- Google Workspace OAuth/SSO remains a deferred hardening option.

## Deferred Architecture Choices

- Exact hosting provider is not selected. Deployment should remain compatible
  with containerized FastAPI/workers, managed PostgreSQL/Redis, and Vercel,
  Cloudflare Pages, or containerized Next.js.
