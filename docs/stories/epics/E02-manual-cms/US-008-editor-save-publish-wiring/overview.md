# Overview

## Current Behavior

US-007 adds a protected Tiptap editor UI, but Save draft and Publish buttons are not wired to the US-006 admin blog API.

## Target Behavior

The editor can save and publish through a Next.js server-side boundary that validates the Better Auth session and creates signed FastAPI admin identity headers. Browser code must not hold or create the admin boundary secret.

## Affected Users

- Internal admins drafting and publishing blog posts.

## Affected Product Docs

- `docs/product/blog-agent.md`
- `docs/product/architecture.md`
- `docs/decisions/0007-admin-auth-strategy.md`

## Non-Goals

- No AI generation.
- No rich media upload.
- No collaboration/comments.
- No client-side direct FastAPI admin calls.
