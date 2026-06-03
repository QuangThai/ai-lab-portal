# Design

## Domain Model

Minimum blog post read model:

- `id`
- `slug`
- `title`
- `excerpt`
- `author_name`
- `status`
- `published_at`
- `content_markdown`

Only `status = "published"` posts are public.

## Application Flow

1. FastAPI exposes the published blog post contract shaped by the PostgreSQL `blog_posts` table.
2. Public list endpoint returns published post summaries sorted newest first.
3. Public detail endpoint returns one published post by slug or `404`.
4. Next.js `/blog` renders the list.
5. Next.js `/blog/[slug]` renders the detail page.

## Interface Contract

FastAPI public endpoints:

- `GET /public/blog-posts`
- `GET /public/blog-posts/{slug}`

Public response payloads must not expose draft/unpublished content. The endpoint contract is stable for future database-backed repository wiring.

## Data Model

Add a `blog_posts` table through Alembic with a unique slug and status field. US-005 includes deterministic seed/read fixture content to prove rendering without introducing admin mutations. Live database persistence is deferred to the next CMS story so CRUD, publish/unpublish, and audit behavior can be implemented together.

## UI / Platform Impact

Adds public blog pages using the existing editorial style guide.

## Observability

No product audit logs because this story has no privileged mutations. Operational request logs already exist.

## Alternatives Considered

1. Typed seed data only.
   - Rejected for long-term CMS direction because admin CRUD/publishing needs PostgreSQL source of truth.
2. Admin CRUD first.
   - Rejected as too broad before read model and public contract exist.
