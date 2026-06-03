# Design

- Keep `BlogRepository` as deterministic in-memory test repository.
- Add `PostgresBlogRepository` using SQLAlchemy Core and project metadata tables.
- `create_app()` uses injected repository when provided; otherwise uses in-memory for `environment="test"` and Postgres for non-test runtime.
- Audit events persist in `audit_events`.

Security remains unchanged: admin mutations still require the US-004 identity boundary.
