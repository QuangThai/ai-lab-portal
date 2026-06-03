# Exec Plan

1. Add SQLAlchemy engine helper.
2. Add Postgres blog repository.
3. Switch non-test app runtime to Postgres.
4. Ensure Playwright backend uses local Docker Postgres URL.
5. Run full verification.

Risk: high-risk due to data persistence, public visibility, admin mutations, and audit records.
