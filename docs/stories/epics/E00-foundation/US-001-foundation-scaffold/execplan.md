# Exec Plan

## Goal

Create the minimum runnable foundation for future AI Lab Portal product slices.

## Scope

In scope:

- Frontend shell scaffold.
- Backend FastAPI scaffold with health endpoint and OpenAPI docs.
- Environment validation.
- PostgreSQL/Alembic setup.
- Redis/Celery smoke setup.
- Structured JSON logging.
- Docker Compose/local development wiring.
- Focused smoke/unit/integration proof.

Out of scope:

- Domain schema and CRUD.
- Auth and authorization.
- Publishing workflows.
- AI calls and prompt registry implementation.
- Crawlers, Firecrawl, Apify, or X/Twitter integrations.

## Risk Classification

Risk flags:

- Data model: database and migrations foundation.
- External systems: Redis, worker runtime, future provider boundaries.
- Public contracts: health endpoint and future API standards.
- Weak proof: no existing app tests or validation commands.
- Multi-domain: frontend, backend, worker, and local runtime are all introduced.

Hard gates:

- Future auth/authorization and provider behavior are explicitly not
  implemented in this story.

## Work Phases

1. Scaffold backend and frontend in the smallest runnable shape.
2. Add environment/config validation and `.env.example` without secrets.
3. Add database migration wiring and empty-db migration proof.
4. Add Redis/Celery worker smoke path.
5. Add structured logging and request id handling.
6. Add Docker Compose/local setup docs.
7. Run and record validation proof.
8. Update Harness story status, proof matrix, and trace.

## Stop Conditions

Pause for human confirmation if:

- Auth strategy becomes necessary to continue.
- Domain schema is needed before foundation proof.
- Tooling requires adding a major dependency not named in the accepted stack.
- Validation requirements need to be weakened.
