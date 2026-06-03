# Exec Plan

## Goal

Add a clean Tiptap-based admin blog editor UI that fits shadcn-style design and prepares the CMS for practical manual publishing.

## Scope

In scope:

- Install minimal Tiptap packages.
- Add editor client component with StarterKit and a compact toolbar.
- Add admin editor page protected by the existing admin auth shell behavior.
- Add title/slug/excerpt fields and status/action panel.
- Add tests for rendering/protection and keep US-006 backend tests green.
- Update Harness evidence.

Out of scope:

- AI generation workflow.
- Collaboration/comments.
- Media uploads.
- Plate/Novel full editor framework adoption.
- Complex publish approval workflow beyond existing US-006 API actions.

## Risk Classification

Risk flags:

- Auth/admin route behavior.
- Public/admin contracts.
- Existing behavior.
- Weak proof until editor E2E/typecheck passes.

Lane: high-risk because this changes privileged admin UI and CMS workflow surface.

## Work Phases

1. Install minimal Tiptap dependencies.
2. Build editor component and admin route.
3. Wire or stub save/publish adapter seam without bypassing US-004/US-006 auth rules.
4. Add/update tests.
5. Run full verification.
6. Update story evidence and trace.

## Stop Conditions

Pause if:

- Editor package installation conflicts with Next.js 16/React 19.
- Save/publish wiring would require weakening auth or using browser-local trust.
- UI scope expands into AI workflow, media storage, or collaboration.
