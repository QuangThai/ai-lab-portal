"""Tests for user-submitted AI news links (US-044, US-045)."""

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
from backend.app.news_extraction import (
    ExtractedArticle,
    ExtractedArticleRepository,
    FakeArticleExtractor,
    content_hash,
)
from backend.app.news_scoring import InMemoryNewsReviewRepository
from backend.app.news_crawl import NewsRawItemRepository
from backend.app.news_sources import NewsSourceRepository
from backend.app.news_submitted_links import (
    InMemorySubmittedLinkRepository,
    SubmittedLinkCreate,
    run_process_submitted_link,
    run_submit_link,
)
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


def _pipeline_deps() -> tuple[
    NewsSourceRepository,
    NewsRawItemRepository,
    ExtractedArticleRepository,
    InMemoryNewsReviewRepository,
    InMemorySubmittedLinkRepository,
]:
    return (
        NewsSourceRepository(),
        NewsRawItemRepository(),
        ExtractedArticleRepository(),
        InMemoryNewsReviewRepository(),
        InMemorySubmittedLinkRepository(),
    )


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
    except ValueError:
        pass


def test_process_marks_duplicate_when_canonical_url_exists() -> None:
    sources, raw, extracted, review, repo = _pipeline_deps()
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
        raw_items=raw,
        sources=sources,
        review=review,
        extractor=FakeArticleExtractor(),
    )
    assert processed.status == "duplicate"


def test_process_runs_extract_score_pipeline() -> None:
    sources, raw, extracted, review, repo = _pipeline_deps()
    submitted = run_submit_link(
        SubmittedLinkCreate(
            url="https://example.com/new-openai-gpt-agent-benchmark",
            note="OpenAI GPT agent benchmark evaluation for enterprise AI teams",
        ),
        repository=repo,
        rate_limit_key_value="ip:test",
    )
    processed = run_process_submitted_link(
        submitted.id,
        repository=repo,
        extracted=extracted,
        raw_items=raw,
        sources=sources,
        review=review,
        extractor=FakeArticleExtractor(),
    )
    assert processed.raw_item_id is not None
    assert processed.status in {"in_review", "submitted"}
    assert extracted.get_by_raw_item_id(processed.raw_item_id) is not None
    if processed.review_item_id:
        assert review.get_by_id(processed.review_item_id) is not None


def test_public_and_admin_submitted_link_endpoints() -> None:
    sources, raw, extracted, review, repo = _pipeline_deps()
    client = TestClient(
        create_app(
            settings=_test_settings(),
            news_source_repository=sources,
            news_raw_item_repository=raw,
            extracted_article_repository=extracted,
            news_review_repository=review,
            submitted_link_repository=repo,
        )
    )

    response = client.post(
        "/public/submitted-links",
        json={
            "url": "https://example.com/interesting-ai-post",
            "note": "LLM agent benchmark results from OpenAI research",
        },
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
    body = processed.json()
    assert body["status"] in {"in_review", "submitted", "duplicate", "failed"}
    assert body.get("raw_item_id")
