# Design

## Domain Model

Entities:

- `BlogPost`: persisted content record with draft/published lifecycle.
- `AuditEvent`: product audit record for privileged admin mutations.
- `AdminIdentity`: validated admin actor from the US-004 boundary.

Blog status values for this slice:

- `draft`
- `published`

## Application Flow

1. Next.js admin code authenticates the user with Better Auth.
2. Next.js server creates signed admin identity headers for FastAPI.
3. FastAPI validates the admin identity at the HTTP boundary.
4. Admin creates or updates a draft blog post.
5. Admin publishes or unpublishes the post.
6. FastAPI writes an audit event for privileged mutations.
7. Public endpoints read only `published` posts from persistence.

## Interface Contract

Candidate admin API endpoints:

- `POST /admin/blog-posts`
- `PATCH /admin/blog-posts/{id}`
- `POST /admin/blog-posts/{id}/publish`
- `POST /admin/blog-posts/{id}/unpublish`

Existing public API endpoints remain:

- `GET /public/blog-posts`
- `GET /public/blog-posts/{slug}`

## Data Model

Use the existing `blog_posts` table from US-005 and add an audit table if one does not already exist.

Audit events should capture at least:

- id
- actor user id
- actor email
- action
- entity type
- entity id
- created timestamp

## UI / Platform Impact

Prefer API-level implementation and tests first. Add minimal admin UI only if needed to prove the flow; a full editor can be a later story.

## Observability

Audit logs are product records and must not be replaced by request logs. Do not log passwords, cookies, secrets, or raw signed identity envelopes.

## Alternatives Considered

1. Full admin editor UI first.
   - Rejected because persistence, authorization, and audit should be proven at API level before UI complexity.
2. Keep seed-only content longer.
   - Rejected because the next durable CMS step needs live persistence.
