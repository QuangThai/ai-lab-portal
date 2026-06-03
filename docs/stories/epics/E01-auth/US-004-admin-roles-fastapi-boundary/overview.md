# Overview

## Current Behavior

The admin shell has a Better Auth login entry point and server-side session check in Next.js. FastAPI still has no authenticated admin boundary, role model, or audit attribution contract for privileged admin mutations.

## Target Behavior

Define and implement the smallest safe bridge for admin identity between Next.js and FastAPI:

- Better Auth remains the MVP authentication boundary in Next.js.
- FastAPI receives authenticated admin identity only through an explicit server-side boundary.
- FastAPI parses and validates identity claims before application code sees them.
- A minimal admin role concept exists before privileged admin mutations are added.
- The story proves the boundary without adding CMS CRUD or publishing behavior.

## Affected Users

- Internal admin users.
- Future backend/API implementers building privileged admin workflows.

## Affected Product Docs

- `docs/product/architecture.md`
- `docs/decisions/0007-admin-auth-strategy.md`

## Non-Goals

- No CMS CRUD.
- No publishing workflow.
- No public content behavior changes.
- No Google Workspace SSO.
- No full enterprise user management.
- No broad permission matrix beyond the minimum role boundary needed for later admin mutations.
