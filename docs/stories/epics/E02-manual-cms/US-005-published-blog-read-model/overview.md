# Overview

## Current Behavior

The portal has foundation shells and admin auth boundaries, but no CMS data model, published blog API, or public blog pages.

## Target Behavior

Create the first long-term CMS slice: a PostgreSQL-backed published blog read model exposed through FastAPI and rendered by public Next.js blog pages.

## Affected Users

- Public visitors reading AI Lab blog content.
- Future admin users who will create and publish posts in later stories.

## Affected Product Docs

- `docs/product/overview.md`
- `docs/product/blog-agent.md`
- `docs/product/mvp-roadmap.md`
- `docs/product/architecture.md`

## Non-Goals

- No admin create/edit/delete UI.
- No publish/unpublish mutation.
- No audit log persistence.
- No AI outline/draft/review workflow.
- No complex tag model beyond minimal display metadata.
