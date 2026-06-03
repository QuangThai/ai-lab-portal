# Exec Plan

## Goal

Move blog CMS from public seed/read contract to live PostgreSQL-backed admin mutations with publish/unpublish and audit attribution.

## Scope

In scope:

- Live database access path for blog posts.
- Admin create/update/publish/unpublish API endpoints.
- Admin identity requirement via US-004 boundary.
- Audit event persistence for privileged mutations.
- Public endpoints reading persisted published posts.
- Backend tests for authorization, persistence, visibility, and audit.
- Keep frontend proof green.

Out of scope:

- Rich editor UI.
- AI drafting/review workflow.
- Tags table and advanced SEO workflow.
- Multi-role permission matrix.

## Risk Classification

Risk flags:

- Auth.
- Authorization.
- Data model.
- Audit/security.
- Public contracts.
- Existing behavior.
- Weak proof until API tests exist.

Hard gates:

- Auth.
- Authorization.
- Data model.
- Audit/security.

Lane: high-risk.

## Work Phases

1. Discovery: inspect DB/session patterns and tests.
2. Design: choose smallest persistence/session approach.
3. Implementation: add repository/endpoints/audit table/tests.
4. Verification: run full configured proof.
5. Harness update: update matrix, evidence, and trace.

## Stop Conditions

Pause if:

- A production database/session architecture decision is needed beyond this slice.
- Audit semantics become ambiguous.
- Public blog API contract would need a breaking change.
- Validation needs to be weakened.
