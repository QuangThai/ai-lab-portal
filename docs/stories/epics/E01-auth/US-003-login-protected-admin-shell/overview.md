# Overview

## Current Behavior

The repository has a Better Auth route/config scaffold for the Next.js frontend, but it does not yet provide a real login UI or protect the admin shell based on an authenticated Better Auth session.

## Target Behavior

The frontend provides the smallest MVP admin authentication experience:

- Admin users have a login entry point.
- Admin shell rendering checks for a Better Auth session before showing privileged admin UI.
- Unauthenticated users are redirected away from protected admin content.
- The slice remains limited to authentication shell behavior.

## Affected Users

- Internal admin users who need to access the admin dashboard.

## Affected Product Docs

- `docs/product/overview.md`
- `docs/product/architecture.md`
- `docs/decisions/0007-admin-auth-strategy.md`

## Non-Goals

- No roles or permission model.
- No admin CRUD.
- No publishing workflow.
- No FastAPI authenticated mutation boundary.
- No audit log attribution.
- No Google Workspace SSO.
