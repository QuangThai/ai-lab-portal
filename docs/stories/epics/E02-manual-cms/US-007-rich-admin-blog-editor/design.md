# Design

## Editor Choice

Use **Tiptap** for the MVP rich editor.

Rationale:

- Headless React editor that works well with custom shadcn-style controls.
- Next.js App Router setup is documented with `useEditor`, `EditorContent`, `StarterKit`, and `immediatelyRender: false` to avoid SSR hydration mismatch.
- Easier to keep the UI clean and editorial than adopting a large prebuilt editor shell.
- Extensible later for AI insertion, claim highlights, review marks, slash commands, and markdown/JSON export.

Alternatives:

- Plate: excellent shadcn integration and AI-ready components, but heavier for this MVP slice.
- Lexical: strong framework, but more plugin/toolbar wiring friction for the first CMS editor.
- Novel: useful inspiration, but too opinionated as a dependency.

## Domain Model

The UI edits the existing blog post fields from US-006:

- title
- slug
- excerpt
- content
- status

## Application Flow

1. Admin opens the blog editor.
2. Next.js verifies the admin session before rendering privileged UI.
3. Editor state is maintained client-side by Tiptap.
4. Save draft sends title/slug/excerpt/content to the admin blog API.
5. Publish/unpublish actions call the existing admin mutation endpoints.
6. The backend records audit events as implemented in US-006.

## Interface Contract

Candidate admin route:

- `/admin/blog/editor`

Tiptap content should be convertible to a backend-safe content format. MVP may store markdown/plain serialized content if the adapter seam is explicit.

## UI / Platform Impact

Use shadcn-style primitives and the existing warm editorial design language:

- calm editor canvas
- compact toolbar
- side panel for status/actions
- no dense dashboard chrome

## Observability

Do not log editor content automatically, passwords, cookies, or signed admin identity headers. Publish actions rely on US-006 audit events.
