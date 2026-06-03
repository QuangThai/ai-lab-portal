# Overview

## Current Behavior

The repository contains Harness operating docs and a large `SPEC.md`, but no
application source code or runnable AI Lab Portal services.

## Target Behavior

The repository has a runnable foundation for later AI Lab Portal slices:
Next.js shell, FastAPI health endpoint, local database/Redis/worker setup,
environment validation, structured logging, and smoke validation.

## Affected Users

- Public visitor, indirectly through future public shell.
- Internal admin/editor/reviewer, indirectly through future admin shell.
- Developer/agent, directly through local setup and validation commands.

## Affected Product Docs

- `docs/product/overview.md`
- `docs/product/architecture.md`
- `docs/product/mvp-roadmap.md`

## Non-Goals

- Authentication or authorization.
- Domain CMS schema and CRUD.
- Blog/news/showcase publishing behavior.
- AI provider calls.
- Crawling or URL fetching.
- X/Twitter ingestion.
