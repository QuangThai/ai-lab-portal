# Overview

## Current Behavior

US-006 proves admin blog CRUD, publish/unpublish, and audit attribution at API level. The admin surface still has no rich editor UI for drafting or publishing blog posts.

## Target Behavior

Provide a clean admin blog editor UI using Tiptap with shadcn-style primitives. The editor should make the manual CMS usable without introducing AI drafting or complex workflow automation.

Minimum target:

- Admin blog editor page/shell.
- Title, slug, excerpt, and rich content editing.
- Minimal toolbar for common editorial formatting.
- Save draft and publish/unpublish actions wired to the admin API boundary or a clear adapter seam.
- UI remains consistent with the AI Lab editorial style guide.

## Affected Users

- Internal admins drafting and publishing AI Lab blog posts.

## Affected Product Docs

- `docs/product/overview.md`
- `docs/product/blog-agent.md`
- `docs/product/style-guide.md`
- `docs/product/architecture.md`

## Non-Goals

- No AI outline/draft/review generation.
- No collaboration/comments.
- No full Plate-style enterprise editor framework.
- No multi-role permission matrix.
- No advanced media/object storage upload flow.
