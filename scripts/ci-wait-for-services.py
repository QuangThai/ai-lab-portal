#!/usr/bin/env python3
"""Wait for PostgreSQL and Redis to become available (CI helper)."""
import os
import time

import psycopg
import redis


def wait_for_postgres(dsn: str, timeout: int = 60) -> None:
    start = time.monotonic()
    while time.monotonic() - start < timeout:
        try:
            conn = psycopg.connect(dsn)
            conn.close()
            print("PostgreSQL ready")
            return
        except Exception as e:
            print(f"Waiting for PostgreSQL... ({e})")
            time.sleep(2)
    raise TimeoutError("PostgreSQL not ready within timeout")


def wait_for_redis(host: str, port: int, timeout: int = 60) -> None:
    start = time.monotonic()
    while time.monotonic() - start < timeout:
        try:
            r = redis.Redis(host=host, port=port)
            r.ping()
            print("Redis ready")
            return
        except Exception as e:
            print(f"Waiting for Redis... ({e})")
            time.sleep(2)
    raise TimeoutError("Redis not ready within timeout")


if __name__ == "__main__":
    pg_dsn = os.environ.get(
        "CI_PG_DSN",
        "dbname=ai_lab_portal_test user=ai_lab_test password=ai_lab_test_password host=localhost port=5432",
    )
    redis_host = os.environ.get("CI_REDIS_HOST", "localhost")
    redis_port = int(os.environ.get("CI_REDIS_PORT", "6379"))

    wait_for_postgres(pg_dsn)
    wait_for_redis(redis_host, redis_port)
    print("All services ready")
