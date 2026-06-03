# Exec Plan

## Scope

- Replace frontend blog seed reads with FastAPI public fetch client.
- Keep public pages free of admin secrets.
- Extend authenticated E2E to assert newly published post appears on `/blog`.
- Run full verification.

## Risk

High-risk: public contract, data visibility, existing behavior, weak proof until E2E passes.
