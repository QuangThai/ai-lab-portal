# Overview

## Current Behavior

Better Auth is configured in the Next.js frontend, but the repository has not accepted a table/migration ownership strategy or deterministic admin seed fixture. Authenticated editor E2E is blocked.

## Target Behavior

Better Auth persistence is explicitly owned by project migrations or a documented generation process, and test/dev can seed a deterministic admin user through a safe path that enables real login E2E.

## Affected Users

- Internal admins.
- Developers/agents validating authenticated admin flows.

## Affected Product Docs

- `docs/product/architecture.md`
- `docs/decisions/0007-admin-auth-strategy.md`
- `docs/stories/epics/E01-auth/US-009-authenticated-editor-e2e-fixture/*`

## Non-Goals

- No production SSO.
- No broad user management UI.
- No auth bypass.
- No browser-exposed secrets.
