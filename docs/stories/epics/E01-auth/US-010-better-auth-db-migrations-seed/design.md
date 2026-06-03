# Design

## Goal

Make Better Auth persistence deterministic enough for real admin login tests while preserving the accepted auth boundary.

## Strategy To Confirm During Research

Preferred:

- Use Better Auth documented CLI/schema generation for PostgreSQL.
- Commit project-owned migration output if it is stable.
- Add a dev/test seed helper that creates a known admin account through Better Auth APIs or documented adapter behavior.

Fallback:

- If generated migration cannot be safely committed yet, document the blocker and add a Harness backlog item rather than inventing an undocumented schema.

## Security Rules

- Seed admin only in development/test/E2E mode.
- No production bypass route.
- No plaintext production password in committed env.
- No browser-local admin boundary secret.

## Validation Shape

- Better Auth route/config still builds.
- Seed helper refuses production.
- E2E can log in using the deterministic admin fixture after schema exists.
