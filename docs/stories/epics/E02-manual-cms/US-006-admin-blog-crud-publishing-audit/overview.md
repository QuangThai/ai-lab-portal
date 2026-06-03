# Overview

## Current Behavior

US-005 introduced the public blog read contract, a `blog_posts` schema, and deterministic public seed content. There is no live database-backed admin CRUD, publish/unpublish mutation, or audit attribution for blog changes.

## Target Behavior

Admin users can manage blog posts through authenticated, role-gated backend mutations backed by PostgreSQL persistence.

Minimum target for this story:

- FastAPI uses live database persistence for blog posts.
- Admin blog create/update endpoints require a validated admin identity.
- Publish/unpublish mutations require admin identity and record audit attribution.
- Public blog endpoints return only published posts from persisted data.

## Affected Users

- Internal admins creating and publishing AI Lab blog posts.
- Public visitors reading published posts.

## Affected Product Docs

- `docs/product/overview.md`
- `docs/product/blog-agent.md`
- `docs/product/mvp-roadmap.md`
- `docs/product/architecture.md`
- `docs/decisions/0007-admin-auth-strategy.md`

## Non-Goals

- No AI draft/outline/review workflow.
- No complex permission matrix beyond the existing `admin` role gate.
- No rich editor UI unless required for a smoke path.
- No tags table unless implementation discovery shows it is required.
