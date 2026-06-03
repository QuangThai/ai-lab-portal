# Overview

## Current Behavior

US-008 wires editor save/publish actions through Next.js server actions and the FastAPI admin boundary. The authenticated browser happy path is not covered by E2E because there is no deterministic Better Auth admin user/session fixture.

## Target Behavior

Provide a safe deterministic admin login fixture so Playwright can prove:

- login succeeds with a known test admin;
- `/admin/blog/editor` renders for an authenticated admin;
- save/publish actions can be exercised without exposing admin boundary secrets to the browser.

## Affected Users

- Internal admins indirectly, through stronger release confidence.
- Future developers/agents relying on E2E proof.

## Affected Product Docs

- `docs/product/architecture.md`
- `docs/decisions/0007-admin-auth-strategy.md`
- `docs/stories/epics/E02-manual-cms/US-008-editor-save-publish-wiring/validation.md`

## Non-Goals

- No production SSO.
- No test-only auth bypass in production bundles.
- No browser-local admin boundary secret.
- No weakening Better Auth session checks.
