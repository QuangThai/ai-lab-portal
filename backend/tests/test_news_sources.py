"""Tests for news source admin API (MVP 3 slice 1)."""

import json
from datetime import UTC, datetime

from fastapi.testclient import TestClient

from backend.app.admin_boundary import (
    ADMIN_IDENTITY_HEADER,
    ADMIN_SIGNATURE_HEADER,
    sign_admin_identity,
)
from backend.app.main import create_app
from backend.app.news_sources import NewsSourceRepository
from backend.app.settings import Settings

TEST_SECRET = "test-admin-boundary-secret-at-least-32-chars"


def _test_settings() -> Settings:
    return Settings(environment="test", admin_boundary_secret=TEST_SECRET)


def _admin_headers() -> dict[str, str]:
    payload = json.dumps(
        {
            "user_id": "user_123",
            "email": "admin@example.com",
            "role": "admin",
            "issued_at": int(datetime.now(UTC).timestamp()),
        }
    )
    return {
        ADMIN_IDENTITY_HEADER: payload,
        ADMIN_SIGNATURE_HEADER: sign_admin_identity(payload, TEST_SECRET),
    }


def test_list_news_sources_returns_seeded_defaults() -> None:
    app = create_app(settings=_test_settings())
    items = TestClient(app).get("/admin/news-sources", headers=_admin_headers()).json()
    assert len(items) >= 1
    assert items[0]["source_type"] in {"rss", "github", "website"}


def test_create_and_update_news_source() -> None:
    repo = NewsSourceRepository(sources=[])
    client = TestClient(create_app(settings=_test_settings(), news_source_repository=repo))
    created = client.post(
        "/admin/news-sources",
        headers=_admin_headers(),
        json={
            "name": "Hacker News AI",
            "source_type": "rss",
            "url_or_identifier": "https://hnrss.org/newest?q=AI",
            "priority": "medium",
            "is_enabled": True,
        },
    )
    assert created.status_code == 200
    source_id = created.json()["id"]
    updated = client.patch(
        f"/admin/news-sources/{source_id}",
        headers=_admin_headers(),
        json={"is_enabled": False, "priority": "low"},
    )
    assert updated.status_code == 200
    assert updated.json()["is_enabled"] is False
    assert updated.json()["priority"] == "low"
