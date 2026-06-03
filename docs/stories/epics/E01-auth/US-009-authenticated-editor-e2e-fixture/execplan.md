# Exec Plan

## Goal

Add deterministic authenticated editor E2E coverage using the real Better Auth path, not a production-visible bypass.

## Scope

In scope:

- Inspect Better Auth route/schema/test utilities.
- Choose fixture strategy.
- Add deterministic admin fixture or documented test session helper.
- Add authenticated editor E2E coverage.
- Run full verification and update Harness evidence.

Out of scope:

- Production SSO.
- Broad user management.
- Role administration UI.
- Test-only bypasses that can run in production.

## Risk Classification

Risk flags:

- Auth.
- Authorization.
- Data model.
- Audit/security.
- Existing behavior.
- Weak proof.

Lane: high-risk.

## Stop Conditions

Pause for human confirmation if:

- The only practical path is a test bypass instead of a real Better Auth session.
- Better Auth schema seeding requires undocumented assumptions.
- Validation would need to be weakened.
