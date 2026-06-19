"""Tests for page view tracking (US-103)."""

from __future__ import annotations

from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import AsyncClient, ASGITransport

from backend.app.page_views import (
    InMemoryPageViewRepository,
    PageView,
    PageViewCreate,
    _check_throttle,
    _hash_ip,
)


class TestPageViewHashing:
    """IP hashing for privacy-safe storage."""

    def test_hash_ip_sha256(self):
        h = _hash_ip("127.0.0.1")
        assert isinstance(h, str)
        assert len(h) == 64  # SHA-256 hex

    def test_hash_ip_deterministic(self):
        assert _hash_ip("192.168.1.1") == _hash_ip("192.168.1.1")

    def test_hash_ip_different(self):
        assert _hash_ip("127.0.0.1") != _hash_ip("192.168.1.1")


class TestPageViewThrottle:
    """Client-side throttle should prevent duplicate views within window."""

    def test_allows_first_view(self):
        assert _check_throttle("s1", "/blog", window_seconds=30) is True

    def test_blocks_duplicate_within_window(self):
        _check_throttle("s1", "/blog", window_seconds=30)
        assert _check_throttle("s1", "/blog", window_seconds=30) is False

    def test_allows_different_paths(self):
        _check_throttle("s1", "/blog", window_seconds=30)
        assert _check_throttle("s1", "/about", window_seconds=30) is True

    def test_allows_different_sessions(self):
        _check_throttle("s1", "/blog", window_seconds=30)
        assert _check_throttle("s2", "/blog", window_seconds=30) is True

    def test_resets_after_window(self):
        _check_throttle("s1", "/blog", window_seconds=0)  # 0s window means always allowed
        assert _check_throttle("s1", "/blog", window_seconds=0) is True


class TestInMemoryPageViewRepository:
    """InMemoryPageViewRepository CRUD operations."""

    @pytest.fixture
    def repo(self):
        return InMemoryPageViewRepository()

    def make_view(self, path: str, session_id: str = "s1", **kwargs):
        now = kwargs.pop("created_at", datetime.now(UTC))
        return PageView(
            id=f"pv-{path}-{session_id}",
            path=path,
            session_id=session_id,
            created_at=now,
            **kwargs,
        )

    def test_create_and_count(self, repo):
        view = self.make_view("/blog")
        repo.create(view)
        assert repo.count_total() == 1

    def test_count_by_path(self, repo):
        repo.create(self.make_view("/blog", "s1"))
        repo.create(self.make_view("/blog", "s2"))
        repo.create(self.make_view("/about", "s1"))

        assert repo.count_by_path("/blog") == 2
        assert repo.count_by_path("/about") == 1
        assert repo.count_by_path("/nonexistent") == 0

    def test_count_total(self, repo):
        repo.create(self.make_view("/a"))
        repo.create(self.make_view("/b"))
        repo.create(self.make_view("/c"))
        assert repo.count_total() == 3

    def test_count_total_since(self, repo):
        old = datetime.now(UTC) - timedelta(hours=2)
        recent = datetime.now(UTC)

        repo.create(self.make_view("/a", created_at=old))
        repo.create(self.make_view("/b", created_at=recent))

        since = datetime.now(UTC) - timedelta(hours=1)
        assert repo.count_total(since=since) == 1

    def test_distinct_sessions(self, repo):
        repo.create(self.make_view("/a", "s1"))
        repo.create(self.make_view("/b", "s1"))
        repo.create(self.make_view("/c", "s2"))

        assert repo.distinct_sessions() == 2

    def test_distinct_sessions_since(self, repo):
        old = datetime.now(UTC) - timedelta(hours=2)
        recent = datetime.now(UTC)

        repo.create(self.make_view("/a", "s1", created_at=old))
        repo.create(self.make_view("/b", "s2", created_at=recent))

        since = datetime.now(UTC) - timedelta(hours=1)
        assert repo.distinct_sessions(since=since) == 1

    def test_empty_repo(self, repo):
        assert repo.count_total() == 0
        assert repo.distinct_sessions() == 0
        assert repo.count_by_path("/anything") == 0


class TestPageViewCreateModel:
    """Pydantic model validation."""

    def test_valid_payload(self):
        view = PageViewCreate(path="/blog", session_id="abc-123")
        assert view.path == "/blog"
        assert view.session_id == "abc-123"
        assert view.referrer is None

    def test_with_optional_fields(self):
        view = PageViewCreate(
            path="/blog",
            session_id="abc-123",
            referrer="https://example.com",
            viewport_width=1920,
            viewport_height=1080,
        )
        assert view.referrer == "https://example.com"
        assert view.viewport_width == 1920

    def test_path_required(self):
        with pytest.raises(ValueError, match="Field required"):
            PageViewCreate(session_id="abc-123")  # type: ignore[call-arg]


class TestPageViewModel:
    """Full page view model (with id and timestamps)."""

    def test_page_view_from_create(self):
        create = PageViewCreate(path="/blog", session_id="s1")
        view = PageView(
            id="pv-1",
            path=create.path,
            session_id=create.session_id,
            created_at=datetime.now(UTC),
            ip_hash=_hash_ip("127.0.0.1"),
        )
        assert view.id == "pv-1"
        assert view.ip_hash == _hash_ip("127.0.0.1")
        assert view.created_at is not None


# ── Integration tests (minimal app, following test_streaming_routes pattern) ──


@pytest.fixture
def page_view_app() -> FastAPI:
    """Build a minimal FastAPI app with only the page-view router."""
    from backend.app.page_views import router

    app = FastAPI()
    app.include_router(router)
    return app


@pytest_asyncio.fixture
async def pv_client(page_view_app: FastAPI) -> AsyncIterator[AsyncClient]:
    """Async test client using the minimal page-view app."""
    transport = ASGITransport(app=page_view_app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.mark.asyncio
async def test_api_record_page_view_returns_200(pv_client: AsyncClient) -> None:
    """POST /api/page-view with full payload returns 200."""
    response = await pv_client.post(
        "/api/page-view",
        json={
            "path": "/integration-test",
            "session_id": "int-test-session",
            "referrer": "https://example.com",
            "viewport_width": 1920,
            "viewport_height": 1080,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert data["throttled"] is False


@pytest.mark.asyncio
async def test_api_record_page_view_minimal_payload(pv_client: AsyncClient) -> None:
    """POST /api/page-view with only required fields returns 200."""
    response = await pv_client.post(
        "/api/page-view",
        json={"path": "/minimal-test", "session_id": "minimal-session"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert data["throttled"] is False


@pytest.mark.asyncio
async def test_api_record_page_view_invalid_payload(pv_client: AsyncClient) -> None:
    """POST /api/page-view with missing required fields returns 422."""
    response = await pv_client.post("/api/page-view", json={})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_api_record_page_view_throttle(pv_client: AsyncClient) -> None:
    """Same session + path within window should be throttled."""
    # First request — allowed
    r1 = await pv_client.post(
        "/api/page-view",
        json={"path": "/throttle-test", "session_id": "throttle-session"},
    )
    assert r1.json()["throttled"] is False

    # Second request (same session + path, within 30s window) — throttled
    r2 = await pv_client.post(
        "/api/page-view",
        json={"path": "/throttle-test", "session_id": "throttle-session"},
    )
    assert r2.json()["throttled"] is True
