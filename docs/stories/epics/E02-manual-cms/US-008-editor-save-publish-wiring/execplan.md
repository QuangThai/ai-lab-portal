# Exec Plan

## Goal

Wire the rich editor Save draft and Publish actions through the accepted server-side identity boundary.

## Scope

In scope:

- Add server-side admin blog API adapter/action.
- Connect editor form/buttons to the adapter seam.
- Preserve Better Auth session check before privileged calls.
- Keep backend API and frontend verification green.

Out of scope:

- AI workflow.
- Media upload.
- Collaboration/comments.
- Direct browser-to-FastAPI admin calls.

## Risk Classification

Risk flags:

- Auth.
- Authorization.
- Audit/security.
- Public/admin contract.
- Existing behavior.

Lane: high-risk.

## Stop Conditions

Pause if save/publish requires browser-local admin secrets or weakening the US-004 boundary.
