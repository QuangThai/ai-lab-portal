# Design

## Domain Model

No domain entities are introduced in the foundation scaffold. This story only
creates runtime, configuration, and smoke-test infrastructure.

## Application Flow

- Backend parses environment settings on startup.
- `GET /health` returns a minimal health response.
- A worker smoke task verifies queue execution.
- Alembic verifies migration wiring against an empty database.
- Frontend renders base public/admin shells without domain data.

## Interface Contract

- `GET /health`
  - Success: service reports healthy status and basic dependency state where
    implemented.
  - Errors: use the standard API error envelope once error middleware exists.

## Data Model

- PostgreSQL exists as the primary database.
- Alembic migration folder exists.
- No domain tables are created in this story unless required by migration
  tooling metadata.

## UI / Platform Impact

- Next.js app shell exists for public and admin route groups.
- Docker Compose supports local Postgres and Redis and should include app
  services when practical for the selected scaffold.

## Observability

- Backend emits structured JSON logs.
- Request logs include timestamp, level, request id when known, action/message,
  duration, and status code where available.
- Audit logs are not implemented in this story because no product mutations
  exist yet.

## Alternatives Considered

1. Start with CMS domain tables first.
   - Rejected: foundation must prove runtime, migrations, and workers before
     domain behavior.
2. Start with public marketing pages only.
   - Rejected: the product requires API, workers, and data pipelines; public UI
     alone would not prove the architecture.
