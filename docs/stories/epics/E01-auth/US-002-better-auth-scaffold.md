# US-002 Better Auth Scaffold

## Status

implemented

## Lane

high-risk

## Product Contract

Create the minimum Better Auth route/config scaffold for the Next.js admin
surface. This story does not implement real login UI, roles, admin CRUD,
FastAPI admin mutations, audit logs, or production auth-table migrations.

## Relevant Product Docs

- `docs/product/architecture.md`
- `docs/decisions/0007-admin-auth-strategy.md`
- `docs/implementation-skills.md`

## Acceptance Criteria

- Better Auth is installed in `frontend/`.
- Next.js exposes `/api/auth/[...all]` with the official Better Auth Next.js
  route handler adapter.
- Auth configuration has explicit secret, base URL, trusted origin, database,
  email/password, and cookie defaults.
- Local scaffold validation can build without committing real secrets.
- Environment placeholders document required production overrides.
- Existing public and admin shell E2E tests still pass.

## Non-Goals

- No production login screen.
- No user/role management.
- No admin CRUD.
- No FastAPI authenticated mutation boundary.
- No Better Auth production migration/table ownership decision beyond route
  scaffold.

## Evidence

- 2026-06-02 Task 11 Better Auth route/config scaffold:
  `cd frontend && npm run test && npm run typecheck && npm run lint && npm run build && npm run test:e2e` → passed.
  Covers auth environment parsing tests, TypeScript, ESLint, Next.js production
  build with dynamic `/api/auth/[...all]`, and Playwright public/admin shell E2E.
  `npm audit --audit-level=high` → no high/critical blockers after `npm audit fix` upgraded Better Auth/Kysely; remaining advisory is moderate Next/PostCSS with only breaking force-fix available.
- 2026-06-02 Task 12 Better Auth dashboard ownership plugin:
  Installed `@better-auth/infra`, added `dash()` to the Better Auth plugin array,
  added `BETTER_AUTH_API_KEY` placeholders, and allowed the active Cloudflare
  tunnel origin in Next.js dev config. Local `GET /api/auth/dash/validate`
  returns `401 {"message":"Invalid API key"}`, which confirms the dashboard
  endpoint exists and is waiting for the real dashboard API key.

## Follow-Up

- Define and apply Better Auth database schema/migration strategy.
- Add login UI and authenticated admin shell behavior.
- Define Next.js-to-FastAPI authenticated request boundary.
- Define admin roles and audit attribution before privileged mutations.
