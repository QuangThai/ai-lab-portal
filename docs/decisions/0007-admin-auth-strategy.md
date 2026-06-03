# 0007 Admin Auth Strategy

Date: 2026-06-02

## Status

Accepted

## Context

Admin implementation is blocked until the repository chooses an authentication
boundary. The product has a Next.js frontend and FastAPI backend. Admin users
will review, edit, and publish content, so auth and authorization are high-risk:
sessions, identity claims, role checks, audit attribution, and CSRF behavior must
be explicit before CRUD routes exist.

The accepted architecture previously listed Google Workspace OAuth and
FastAPI-managed secure HTTP-only sessions as candidates. The implementation also
needs to consider the user's preference that login can use Better Auth in the
Next.js frontend, and React Query can be introduced later if client-side server
state becomes useful.

## Decision

Use **Better Auth in the Next.js frontend as the MVP authentication boundary**.

- Better Auth owns login routes and session cookie management in Next.js.
- Next.js exposes Better Auth under `/api/auth/[...all]` using the official
  Next.js route handler adapter.
- Better Auth session cookies must be HTTP-only, secure in production, and use
  SameSite protection.
- Admin pages in Next.js must check the Better Auth session before rendering
  privileged admin UI.
- FastAPI remains the system API for domain behavior. When admin API routes are
  added, FastAPI must receive authenticated admin identity through an explicit
  server-side boundary, not through browser-local tokens.
- The backend must parse and validate any identity/session claims at its HTTP
  boundary before application code sees them.
- Authorization remains separate from authentication. Admin role/permission
  checks must be implemented before any privileged mutation, publishing action,
  or audit-attributed workflow.
- React Query is allowed later for admin client-side server state, cache
  invalidation, and mutations after API contracts exist. It is not required for
  the auth decision itself.

Do not implement login, roles, admin CRUD, audit logs, or publishing behavior in
this decision task.

## Alternatives Considered

1. **FastAPI-managed secure HTTP-only sessions**
   - Strong backend ownership and a single auth boundary for APIs.
   - Fits Python API control well.
   - Rejected for MVP because the user explicitly wants the option to use Better
     Auth in the Next.js frontend and because the first admin surface is a
     Next.js app shell.
2. **Google Workspace OAuth first**
   - Strong fit for a company-only admin portal.
   - Useful future hardening option.
   - Deferred because it adds provider configuration and deployment complexity
     before the MVP has admin workflows.
3. **Auth.js with backend JWT validation**
   - Common Next.js pattern.
   - Rejected for now in favor of Better Auth per user preference and current
     Better Auth Next.js support.
4. **Client-stored JWTs in localStorage**
   - Rejected. Client-accessible auth tokens are not acceptable for this admin
     surface.

## Consequences

Positive:

- Aligns with the Next.js admin shell and user preference.
- Keeps auth UX close to the frontend while preserving FastAPI as the domain API.
- Avoids committing to an external identity provider before MVP workflows exist.
- Leaves room for Google Workspace OAuth or SSO as a later Better Auth/provider
  plugin choice.

Tradeoffs:

- The frontend/backend auth bridge must be designed carefully before FastAPI
  admin mutations exist.
- Backend authorization cannot trust client-side state; it needs a server-side
  validated identity boundary.
- Better Auth introduces a TypeScript-side auth dependency and persistence
  requirements that must fit the PostgreSQL-backed architecture.
- Cookie, CSRF, CORS, and deployment origin rules must be verified before admin
  release.

## Follow-Up

- Create the admin auth scaffold story before implementing login.
- Define Better Auth persistence tables/migrations before enabling auth in
  production-like environments.
- Define the Next.js-to-FastAPI authenticated request boundary before admin API
  mutations.
- Define initial admin role model and audit attribution before CMS/publishing
  CRUD.
- Consider React Query only when admin routes need client-side data fetching,
  optimistic updates, or cache invalidation.
- Consider Google Workspace OAuth/SSO as a later hardening decision.
