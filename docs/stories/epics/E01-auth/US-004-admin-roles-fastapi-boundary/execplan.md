# Exec Plan

## Goal

Create the minimum trusted admin identity boundary from Next.js/Better Auth to FastAPI, with a minimal role concept, before any privileged admin product mutation is implemented.

## Scope

In scope:

- Inspect current FastAPI/frontend foundation and auth code.
- Define exact boundary mechanism and endpoint names.
- Add a protected FastAPI admin probe or equivalent smoke endpoint.
- Validate server-provided identity at the FastAPI HTTP boundary.
- Add backend tests for missing/invalid/valid identity.
- Keep frontend auth shell tests passing.
- Update story evidence and Harness matrix.

Out of scope:

- CMS CRUD.
- Publishing actions.
- Audit log persistence.
- Role administration UI.
- Google Workspace SSO.
- Complete permission matrix.

## Risk Classification

Risk flags:

- Auth.
- Authorization.
- Public/admin API contract.
- Audit/security.
- Weak proof until boundary tests exist.

Hard gates:

- Auth.
- Authorization.
- Audit/security.

Lane: high-risk.

## Work Phases

1. Discovery: inspect FastAPI routes/settings/tests and frontend auth/admin patterns.
2. Boundary decision: choose the smallest explicit server-side identity verification mechanism.
3. Human confirmation: pause if multiple security-valid boundary choices remain or if a durable architecture decision is required.
4. Implementation: add boundary parser, probe endpoint, and tests.
5. Verification: run backend and frontend proof commands.
6. Harness update: update matrix/story evidence and trace.

## Stop Conditions

Pause for human confirmation if:

- The boundary would require trusting browser-provided roles or tokens.
- A production role storage/migration decision becomes necessary.
- Existing auth decision `0007` would need to change.
- Validation requirements need to be weakened.
