# Design

## Domain Model

This story does not add domain entities. It only establishes the admin surface authentication shell.

Important distinction:

- Authentication answers whether an admin user has a valid Better Auth session.
- Authorization is not implemented here and must be designed before privileged mutations.

## Application Flow

1. User visits protected admin content.
2. Next.js checks the Better Auth session at the server boundary before rendering privileged admin UI.
3. If no session exists, Next.js redirects to the login entry point.
4. Login UI submits credentials to the existing Better Auth route handler.
5. After successful login, the user returns to the admin shell.

## Interface Contract

Frontend routes:

- `/admin/login`: login entry point.
- `/admin`: protected admin shell/dashboard entry.
- `/api/auth/[...all]`: existing Better Auth route handler.

Errors and unauthenticated states should be user-visible but must not expose secrets, tokens, or internal provider details.

## Data Model

No new product tables are introduced in this story.

Better Auth persistence/migration ownership remains a follow-up unless implementation discovery shows the login slice cannot work safely without it.

## UI / Platform Impact

The public website remains unaffected. The admin surface gains a minimal login page and protected dashboard behavior.

## Observability

No product audit logs are introduced in this story because no privileged product mutation occurs.

Operational logs should not include passwords, secrets, session tokens, or cookies.

## Alternatives Considered

1. Implement roles and admin CRUD in the same slice.
   - Rejected because authorization and audit attribution need a separate design before privileged mutations.
2. Use client-only protection.
   - Rejected because privileged admin UI should be gated by server-side session checks, not browser-local state.
