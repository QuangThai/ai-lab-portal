# Exec Plan

## Goal

Resolve Better Auth database ownership and seed a deterministic admin fixture for real authenticated E2E.

## Scope

In scope:

- Research official Better Auth schema/migration command.
- Decide whether to commit generated migration or document blocker.
- Add dev/test seed helper if safe.
- Keep existing auth and editor tests green.

Out of scope:

- SSO.
- Production user administration.
- Auth bypasses.

## Risk Classification

Risk flags:

- Auth.
- Authorization.
- Data model.
- Audit/security.
- Existing behavior.

Lane: high-risk.

## Stop Conditions

Pause if Better Auth schema requires undocumented assumptions or if only bypass-style login is practical.
