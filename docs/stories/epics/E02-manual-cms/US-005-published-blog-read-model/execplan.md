# Exec Plan

## Goal

Ship the first long-term CMS vertical slice: PostgreSQL-backed published blog read model, FastAPI public read endpoints, and public Next.js blog pages.

## Scope

In scope:

- Minimal `blog_posts` schema/migration.
- Published-only FastAPI list/detail endpoints.
- Backend tests for public filtering and missing/draft detail behavior.
- Public `/blog` and `/blog/[slug]` pages.
- E2E smoke coverage for public blog pages.
- Harness matrix/story evidence updates.

Out of scope:

- Admin CRUD.
- Publishing mutations.
- Audit logs.
- AI generation workflow.
- Complex tags/categories.

## Risk Classification

Risk flags:

- Data model.
- Public contracts.
- Existing behavior/public routes.
- Weak proof until API and E2E tests exist.

Lane: high-risk.

## Work Phases

1. Inspect current migration/database patterns.
2. Add minimal schema and seed/read repository shape.
3. Add public API endpoints and tests.
4. Add public blog pages and tests.
5. Run full verification.
6. Update Harness evidence and trace.

## Stop Conditions

Pause if:

- Admin mutation/audit semantics become necessary.
- Migration strategy conflicts with current foundation setup.
- API contract expands beyond published read-only behavior.
