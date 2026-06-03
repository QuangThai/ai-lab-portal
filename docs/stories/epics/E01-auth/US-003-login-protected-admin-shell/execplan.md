# Exec Plan

## Goal

Ship the smallest safe admin authentication shell slice after the Better Auth scaffold: a login entry point and protected admin shell behavior.

## Scope

In scope:

- Create or update the `/admin/login` route.
- Protect the `/admin` shell with a server-side Better Auth session check.
- Redirect unauthenticated admin users to login.
- Add/update tests for unauthenticated protection and login page rendering.
- Keep Harness matrix/story proof current.

Out of scope:

- Roles and permissions.
- Admin CRUD.
- Publishing workflow.
- FastAPI authenticated mutation boundary.
- Audit log attribution.
- Production SSO.

## Risk Classification

Risk flags:

- Auth.
- Public contracts/admin-visible route behavior.
- Weak proof until E2E coverage is added.

Hard gates:

- Auth.

Lane: high-risk.

## Work Phases

1. Discovery: inspect current frontend auth config, admin routes, and tests.
2. Design check: confirm the minimal login/protection route shape.
3. Validation planning: identify exact unit/type/lint/build/E2E commands.
4. Implementation: make the smallest frontend route/test changes.
5. Verification: run frontend checks and update evidence.
6. Harness update: update matrix/story status and record trace.

## Stop Conditions

Pause for human confirmation if:

- Implementing this slice requires adding roles, authorization, or audit semantics.
- Better Auth production table ownership must be decided before any safe local login behavior works.
- Validation requirements need to be weakened.
- The accepted Next.js/Better Auth auth boundary changes.
