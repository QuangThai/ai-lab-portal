"""Tests for user-submitted AI news links (US-044)."""

from __future__ import annotations

import json
from datetime import UTC, datetime

from fastapi.testclient import TestClient

from backend.app.admin_boundary import (
    ADMIN_IDENTITY_HEADER,
    ADMIN_SIGNATURE_HEADER,
    sign_admin_identity,
)
from backend.app.main import create_app
from backend.app.news_extraction import ExtractedArticle, ExtractedArticleRepository, content_hash
from backend.app.news_submitted_links import InMemorySubmittedLinkRepository, run_process_submitted_link, run_submit_link, SubmittedLinkCreate
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


def test_submit_link_idempotent_by_normalized_url() -> None:
    repo = InMemorySubmittedLinkRepository()
    payload = SubmittedLinkCreate(url="https://example.com/article?utm_source=x")
    first = run_submit_link(payload, repository=repo, rate_limit_key_value="ip:test")
    second = run_submit_link(payload, repository=repo, rate_limit_key_value="ip:test")
    assert first.duplicate is False
    assert second.duplicate is True
    assert first.id == second.id


def test_submit_link_rejects_unsafe_url() -> None:
    repo = InMemorySubmittedLinkRepository()
    payload = SubmittedLinkCreate(url="http://127.0.0.1/private")
    try:
        run_submit_link(payload, repository=repo, rate_limit_key_value="ip:test")
        raise AssertionError("expected ValueError")
    except ValueError as exc:
        assert "Blocked" in str(exc) or "127.0.0.1" in str(exc)


def test_process_marks_duplicate_when_canonical_url_exists() -> None:
    repo = InMemorySubmittedLinkRepository()
    extracted = ExtractedArticleRepository()
    now = datetime.now(UTC)
    extracted._rows["ext1"] = ExtractedArticle(
        id="ext1",
        raw_item_id="raw1",
        source_url="https://example.com/article",
        final_url="https://example.com/article",
        canonical_url="https://example.com/article",
        title="Existing",
        content_markdown="# Existing",
        content_text="Existing",
        content_hash=content_hash("# Existing", "Existing"),
        provider="fake",
        extraction_status="success",
        extracted_at=now,
        canonical_url_normalized="https://example.com/article",
    )
    submitted = run_submit_link(
        SubmittedLinkCreate(url="https://example.com/article/"),
        repository=repo,
        rate_limit_key_value="ip:test",
    )
    processed = run_process_submitted_link(
        submitted.id,
        repository=repo,
        extracted=extracted,
    )
    assert processed.status == "duplicate"


def test_public_and_admin_submitted_link_endpoints() -> None:
    repo = InMemorySubmittedLinkRepository()
    client = TestClient(create_app(settings=_test_settings(), submitted_link_repository=repo))

    response = client.post(
        "/public/submitted-links",
        json={"url": "https://example.com/interesting-ai-post"},
    )
    assert response.status_code == 200
    submission_id = response.json()["id"]

    listed = client.get("/admin/news/submitted-links", headers=_admin_headers())
    assert listed.status_code == 200
    assert any(row["id"] == submission_id for row in listed.json())

    processed = client.post(
        f"/admin/news/submitted-links/{submission_id}/process",
        headers=_admin_headers(),
    )
    assert processed.status_code == 200
    assert processed.json()["status"] in {"submitted", "duplicate", "failed"}
