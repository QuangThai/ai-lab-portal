"""Postgres-backed integration tests for AI agent features (US-107/108/109).

These tests use real Postgres via Docker compose (port 15432) instead of
in-memory repositories. They verify database state, SQL queries, and API
contracts for the content repurpose, auto-scheduling, and SEO optimize agents.

Requires `docker compose up -d postgres` running with alembic migrations applied.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import time
from collections.abc import AsyncIterator
from datetime import datetime, timezone
from uuid import uuid4

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import AsyncClient, ASGITransport
from sqlalchemy import Engine, NullPool, create_engine, text
from backend.app.admin_boundary import ADMIN_IDENTITY_HEADER, ADMIN_SIGNATURE_HEADER
from backend.app.blog import PostgresBlogRepository
from backend.app.blog_ideas import PostgresBlogIdeaRepository
from backend.app.content_repurpose import FakeContentRepurposeService
from backend.app.content_repurpose_routes import create_content_repurpose_routes
from backend.app.scheduling_agent import FakeSchedulingService
from backend.app.scheduling_routes import (
    create_scheduling_routes,
    create_blog_idea_scheduling_routes,
)
from backend.app.seo_optimizer import FakeSeoOptimizerService
from backend.app.seo_optimizer_routes import create_seo_optimizer_routes
from backend.app.settings import Settings

# ── Test Database Setup ──────────────────────────────────────────────

_TEST_DB_URL = "postgresql+psycopg://ai_lab:ai_lab_secret@127.0.0.1:15432/ai_lab"


@pytest.fixture(scope="module")
def db_engine() -> Engine:
    """Module-scoped Postgres engine.

    Tests are skipped if Postgres is not available.
    """
    try:
        engine = create_engine(_TEST_DB_URL, poolclass=NullPool)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return engine
    except Exception:
        pytest.skip("Postgres not available — start Docker compose")


@pytest.fixture(scope="module")
def settings() -> Settings:
    return Settings(
        environment="test",
        llm_backend="agents_sdk",
        llm_model="gpt-4o",
        admin_boundary_secret="test-secret-at-least-32-characters-long!!",
    )


@pytest.fixture
def auth_headers(settings: Settings) -> dict[str, str]:
    now = int(time.time())
    identity_payload = json.dumps(
        {"user_id": "admin_1", "email": "admin@test.com", "role": "admin", "issued_at": now},
        separators=(",", ":"),
    )
    secret = settings.admin_boundary_secret.get_secret_value()
    signature = hmac.new(
        secret.encode("utf-8"),
        identity_payload.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return {
        ADMIN_IDENTITY_HEADER: identity_payload,
        ADMIN_SIGNATURE_HEADER: signature,
    }


# ── US-107: Content Repurpose Agent ──────────────────────────────────


@pytest_asyncio.fixture
async def repurpose_test_data(db_engine: Engine) -> AsyncIterator[dict]:
    """Create a published blog post in Postgres for repurpose tests.

    Cleans up after the test completes.
    """
    post_id = f"db-repurpose-{uuid4().hex[:8]}"
    slug = f"db-repurpose-{uuid4().hex[:8]}"
    now = datetime.now(timezone.utc)

    with db_engine.begin() as conn:
        conn.execute(
            text("""
                INSERT INTO blog_posts (id, slug, title, excerpt, content_markdown, status, author_name, published_at, created_at, updated_at)
                VALUES (:id, :slug, :title, :excerpt, :content, 'published', 'test-author', :published_at, :now, :now)
            """),
            {
                "id": post_id,
                "slug": slug,
                "title": f"DB Repurpose Test {post_id}",
                "excerpt": "Test excerpt for DB repurpose",
                "content": "# DB Repurpose\n\nContent for Postgres-backed integration test.",
                "published_at": now,
                "now": now,
            },
        )

    yield {"post_id": post_id, "slug": slug}

    with db_engine.begin() as conn:
        conn.execute(text("DELETE FROM blog_posts WHERE id = :id"), {"id": post_id})


@pytest.mark.asyncio
async def test_us107_repurpose_with_postgres(
    db_engine: Engine,
    settings: Settings,
    auth_headers: dict[str, str],
    repurpose_test_data: dict,
) -> None:
    """US-107: Content repurpose works with real Postgres data."""
    repo = PostgresBlogRepository(db_engine)
    service = FakeContentRepurposeService()
    router = create_content_repurpose_routes(service, repo, settings)

    app = FastAPI()
    app.include_router(router)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            f"/admin/blog-posts/{repurpose_test_data['post_id']}/repurpose",
            headers=auth_headers,
        )

    assert response.status_code == 200
    data = response.json()
    assert data["blog_post_id"] == repurpose_test_data["post_id"]
    assert "id" in data
    assert "twitter_thread" in data
    assert "linkedin_article" in data
    assert "summary_snippet" in data


@pytest.mark.asyncio
async def test_us107_repurpose_missing_post_404(
    db_engine: Engine,
    settings: Settings,
    auth_headers: dict[str, str],
) -> None:
    """US-107: Repurposing a non-existent post returns 404."""
    repo = PostgresBlogRepository(db_engine)
    service = FakeContentRepurposeService()
    router = create_content_repurpose_routes(service, repo, settings)

    app = FastAPI()
    app.include_router(router)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/admin/blog-posts/nonexistent-post-id/repurpose",
            headers=auth_headers,
        )

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


# ── US-108: Auto-Scheduling Agent ─────────────────────────────────────


@pytest_asyncio.fixture
async def scheduling_post_data(db_engine: Engine) -> AsyncIterator[dict]:
    """Create a published blog post and a blog idea in Postgres."""
    post_id = f"db-sched-{uuid4().hex[:8]}"
    idea_id = f"db-sched-idea-{uuid4().hex[:8]}"
    slug = f"db-sched-{uuid4().hex[:8]}"
    now = datetime.now(timezone.utc)

    with db_engine.begin() as conn:
        conn.execute(
            text("""
                INSERT INTO blog_posts (id, slug, title, excerpt, content_markdown, status, author_name, published_at, created_at, updated_at)
                VALUES (:id, :slug, :title, :excerpt, :content, 'published', 'test-author', :published_at, :now, :now)
            """),
            {
                "id": post_id,
                "slug": slug,
                "title": f"DB Scheduling Test {post_id}",
                "excerpt": "Scheduling test excerpt",
                "content": "# Scheduling\n\nContent for scheduling test.",
                "published_at": now,
                "now": now,
            },
        )
        conn.execute(
            text("""
                INSERT INTO blog_ideas (id, title, angle, source, status, created_at, updated_at)
                VALUES (:id, :title, 'test-angle', 'test', 'approved', :now, :now)
            """),
            {
                "id": idea_id,
                "title": f"DB Scheduling Idea {idea_id}",
                "now": now,
            },
        )

    yield {"post_id": post_id, "idea_id": idea_id, "slug": slug}

    with db_engine.begin() as conn:
        conn.execute(text("DELETE FROM blog_ideas WHERE id = :id"), {"id": idea_id})
        conn.execute(text("DELETE FROM blog_posts WHERE id = :id"), {"id": post_id})


@pytest.mark.asyncio
async def test_us108_schedule_post_with_postgres(
    db_engine: Engine,
    settings: Settings,
    auth_headers: dict[str, str],
    scheduling_post_data: dict,
) -> None:
    """US-108: Auto-scheduling for blog post works with Postgres data."""
    repo = PostgresBlogRepository(db_engine)
    service = FakeSchedulingService()
    router = create_scheduling_routes(service, repo, settings)

    app = FastAPI()
    app.include_router(router)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            f"/admin/blog-posts/{scheduling_post_data['post_id']}/suggest-schedule",
            headers=auth_headers,
        )

    assert response.status_code == 200
    data = response.json()
    assert "suggested_date" in data
    assert "suggested_time" in data
    assert "rationale" in data
    assert "confidence" in data


@pytest.mark.asyncio
async def test_us108_schedule_idea_with_postgres(
    db_engine: Engine,
    settings: Settings,
    auth_headers: dict[str, str],
    scheduling_post_data: dict,
) -> None:
    """US-108: Auto-scheduling for blog idea works with Postgres data."""
    ideas_repo = PostgresBlogIdeaRepository(db_engine)
    service = FakeSchedulingService()
    router = create_blog_idea_scheduling_routes(service, ideas_repo, settings)

    app = FastAPI()
    app.include_router(router)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            f"/admin/blog-ideas/{scheduling_post_data['idea_id']}/suggest-schedule",
            headers=auth_headers,
        )

    assert response.status_code == 200
    data = response.json()
    assert "suggested_date" in data
    assert "suggested_time" in data
    assert "rationale" in data


# ── US-109: SEO Auto-Optimize Agent ────────────────────────────────────


@pytest_asyncio.fixture
async def seo_test_data(db_engine: Engine) -> AsyncIterator[dict]:
    """Create a blog idea in Postgres for SEO tests."""
    idea_id = f"db-seo-{uuid4().hex[:8]}"
    now = datetime.now(timezone.utc)

    with db_engine.begin() as conn:
        conn.execute(
            text("""
                INSERT INTO blog_ideas (id, title, angle, source, status, created_at, updated_at)
                VALUES (:id, :title, 'seo-test-angle', 'test', 'approved', :now, :now)
            """),
            {
                "id": idea_id,
                "title": f"DB SEO Test Idea {idea_id}",
                "now": now,
            },
        )

    yield {"idea_id": idea_id}

    with db_engine.begin() as conn:
        conn.execute(text("DELETE FROM blog_ideas WHERE id = :id"), {"id": idea_id})


@pytest.mark.asyncio
async def test_us109_optimize_seo_with_postgres(
    db_engine: Engine,
    settings: Settings,
    auth_headers: dict[str, str],
    seo_test_data: dict,
) -> None:
    """US-109: SEO optimize reads blog idea from Postgres."""
    ideas_repo = PostgresBlogIdeaRepository(db_engine)
    service = FakeSeoOptimizerService()
    router = create_seo_optimizer_routes(service, ideas_repo, settings)

    app = FastAPI()
    app.include_router(router)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            f"/admin/blog-ideas/{seo_test_data['idea_id']}/optimize-seo",
            headers=auth_headers,
        )

    assert response.status_code == 200
    data = response.json()
    assert "changes" in data
    assert "overall_summary" in data
    assert len(data["changes"]) > 0


@pytest.mark.asyncio
async def test_us109_apply_seo_changes_persists_to_db(
    db_engine: Engine,
    settings: Settings,
    auth_headers: dict[str, str],
    seo_test_data: dict,
) -> None:
    """US-109: Applying SEO changes persists the title update to Postgres."""
    ideas_repo = PostgresBlogIdeaRepository(db_engine)
    service = FakeSeoOptimizerService()
    router = create_seo_optimizer_routes(service, ideas_repo, settings)

    app = FastAPI()
    app.include_router(router)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # First get optimization suggestions
        opt_response = await client.post(
            f"/admin/blog-ideas/{seo_test_data['idea_id']}/optimize-seo",
            headers=auth_headers,
        )
        assert opt_response.status_code == 200
        opt_data = opt_response.json()

        # Apply the title change
        title_change = [c for c in opt_data["changes"] if c["section"] == "title"]
        if title_change:
            apply_response = await client.post(
                f"/admin/blog-ideas/{seo_test_data['idea_id']}/apply-seo-changes",
                headers=auth_headers,
                json={"accepted_sections": ["title"]},
            )
            assert apply_response.status_code == 200
            apply_data = apply_response.json()
            assert apply_data["applied_count"] >= 1

            # Verify the title was updated in Postgres
            with db_engine.connect() as conn:
                row = conn.execute(
                    text("SELECT title FROM blog_ideas WHERE id = :id"),
                    {"id": seo_test_data["idea_id"]},
                ).mappings().one_or_none()
                assert row is not None
                assert row["title"] == title_change[0]["after"]
