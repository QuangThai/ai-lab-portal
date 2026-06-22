"""Test fixtures for DB-backed integration tests.

Requires Docker Postgres running on localhost:15432 (from docker compose).
Tests using postgres_db are skipped automatically if Postgres is not available.
"""

from __future__ import annotations

import os
from collections.abc import Iterator

import pytest
from sqlalchemy import Engine, NullPool, create_engine, text

# Database URL for integration tests — uses Docker compose Postgres
_TEST_DB_URL = os.environ.get(
    "AI_LAB_TEST_DATABASE_URL",
    "postgresql+psycopg://ai_lab:ai_lab_secret@127.0.0.1:15432/ai_lab",
)


def _postgres_available() -> bool:
    """Check if Postgres is reachable on the test URL."""
    try:
        engine = create_engine(_TEST_DB_URL, poolclass=NullPool)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        engine.dispose()
        return True
    except Exception:
        return False


@pytest.fixture(scope="session")
def postgres_db() -> Iterator[Engine]:
    """Session-scoped Postgres engine.

    Uses the Docker compose Postgres directly (migrations must be run
    separately via `alembic upgrade head` or `docker compose up -d`).

    Skips tests if Postgres is not available.
    """
    if not _postgres_available():
        pytest.skip("Postgres not available — start Docker and run compose")

    engine = create_engine(_TEST_DB_URL, poolclass=NullPool)
    yield engine
    engine.dispose()
