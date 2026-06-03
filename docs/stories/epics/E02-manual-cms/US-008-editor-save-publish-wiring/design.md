# Design

## Boundary Rule

Browser code must not sign FastAPI admin identity headers. The flow is:

1. Client editor submits content to a Next.js server action or route handler.
2. Next.js checks the Better Auth session server-side.
3. Next.js creates signed admin identity headers using `ADMIN_BOUNDARY_SECRET`.
4. Next.js calls FastAPI admin blog endpoints.
5. FastAPI validates headers and records audit events.

## Interface Contract

Frontend adapter functions should support:

- create draft blog post
- update draft blog post if an id exists
- publish blog post after save

## Data Contract

Editor payload:

- title
- slug
- excerpt
- content markdown/plain text

## UI Impact

The editor status panel shows save/publish feedback without exposing secrets.

## Alternatives Considered

1. Browser calls FastAPI with signed headers.
   - Rejected because the browser must not access the boundary secret.
2. Leave buttons as static UI.
   - Rejected because US-008 is specifically the wiring slice.
